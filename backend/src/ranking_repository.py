"""Persistencia transacional dos rankings mutaveis do vestibular."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from .constants import (
    ENTRY_MODE_PATTERNS,
    RANKING_DB_PATH,
    RANKING_MIN_COMPLETENESS_RATIO,
    RANKING_MIN_DETAIL_YEAR,
    STATUS_PATTERNS,
)


TRACKED_FIELDS = (
    "final_score",
    "remapped_vacancy",
    "competition_vacancies",
    "entry_vacancy",
    "entry_mode",
    "status",
    "status_date",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def candidate_key(year: int | str, course: str, registration: str) -> str:
    """Gera uma identidade estavel sem persistir a inscricao publicada."""
    value = f"{year}|{course.strip()}|{registration.strip()}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def normalize_entry_mode(value: str) -> str:
    for mode, pattern in ENTRY_MODE_PATTERNS.items():
        if re.search(pattern, value or ""):
            return mode
    return (value or "").strip()


class RankingRepository:
    def __init__(self, path: str | Path = RANKING_DB_PATH):
        self.path = Path(path)

    @contextmanager
    def connect(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self, legacy_json_path: str | Path | None = None) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                PRAGMA journal_mode = WAL;

                CREATE TABLE IF NOT EXISTS candidate_current (
                    candidate_key TEXT PRIMARY KEY,
                    year INTEGER NOT NULL,
                    course TEXT NOT NULL,
                    source_course TEXT,
                    source_classification TEXT,
                    name TEXT,
                    final_score REAL NOT NULL,
                    remapped_vacancy TEXT,
                    competition_vacancies TEXT,
                    entry_vacancy TEXT NOT NULL,
                    entry_mode TEXT NOT NULL,
                    status TEXT NOT NULL,
                    status_date TEXT,
                    collected_at TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    missing_runs INTEGER NOT NULL DEFAULT 0,
                    detailed INTEGER NOT NULL DEFAULT 1
                );

                CREATE INDEX IF NOT EXISTS idx_candidate_ranking
                    ON candidate_current(year, course, entry_mode, active, detailed, final_score DESC);
                CREATE INDEX IF NOT EXISTS idx_candidate_cutoff
                    ON candidate_current(year, course, entry_mode, active, final_score);

                CREATE TABLE IF NOT EXISTS ranking_aggregate (
                    year INTEGER NOT NULL,
                    course TEXT NOT NULL,
                    entry_mode TEXT NOT NULL,
                    cutoff REAL NOT NULL,
                    source TEXT NOT NULL,
                    PRIMARY KEY (year, course, entry_mode)
                );

                CREATE TABLE IF NOT EXISTS candidate_change (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_key TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    course TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    changed_fields TEXT NOT NULL,
                    before_json TEXT NOT NULL,
                    after_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sync_run (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    years TEXT NOT NULL,
                    courses_processed INTEGER NOT NULL DEFAULT 0,
                    failures INTEGER NOT NULL DEFAULT 0,
                    error_summary TEXT
                );

                CREATE TABLE IF NOT EXISTS sync_course_run (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL REFERENCES sync_run(id),
                    year INTEGER NOT NULL,
                    course TEXT NOT NULL,
                    status TEXT NOT NULL,
                    row_count INTEGER NOT NULL DEFAULT 0,
                    error TEXT,
                    finished_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_sync_course_latest
                    ON sync_course_run(year, course, finished_at DESC);

                CREATE TABLE IF NOT EXISTS sync_lock (
                    name TEXT PRIMARY KEY,
                    owner TEXT NOT NULL,
                    acquired_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS ranking_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                """
            )
            connection.commit()

        if legacy_json_path:
            self.import_legacy_json_once(legacy_json_path)
        self.compact_pre2022_data()

    def compact_pre2022_data(self) -> None:
        """Mantém anos antigos apenas como cortes agregados, sem linhas individuais."""
        status_filters = " OR ".join("status LIKE ?" for _ in STATUS_PATTERNS)
        params = [RANKING_MIN_DETAIL_YEAR, *[f"%{value}%" for value in STATUS_PATTERNS]]
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT year, course, entry_mode, MIN(final_score) AS cutoff
                FROM candidate_current
                WHERE year < ? AND active = 1 AND ({status_filters})
                GROUP BY year, course, entry_mode
                """,
                params,
            ).fetchall()
            connection.executemany(
                """
                INSERT INTO ranking_aggregate(year, course, entry_mode, cutoff, source)
                VALUES (?, ?, ?, ?, 'legacy-json')
                ON CONFLICT(year, course, entry_mode) DO UPDATE SET cutoff = excluded.cutoff
                """,
                [(row["year"], row["course"], row["entry_mode"], row["cutoff"]) for row in rows],
            )
            connection.execute(
                "DELETE FROM candidate_current WHERE year < ?",
                (RANKING_MIN_DETAIL_YEAR,),
            )
            connection.commit()

    def import_legacy_json_once(self, legacy_json_path: str | Path) -> int:
        path = Path(legacy_json_path)
        if not path.exists():
            return 0

        with self.connect() as connection:
            # API e scheduler podem subir juntos; o lock transacional garante
            # que apenas um processo execute o bootstrap legado.
            connection.execute("BEGIN IMMEDIATE")
            marker = connection.execute(
                "SELECT value FROM ranking_meta WHERE key = 'legacy_imported'"
            ).fetchone()
            if marker:
                connection.rollback()
                return 0

            with path.open("r", encoding="utf-8") as source:
                rows = json.load(source)

            collected_at = utc_now()
            records = []
            for index, row in enumerate(rows):
                year = int(row["ano"])
                course = row["curso"]
                entry_vacancy = row.get("modalidade", "")
                identity = hashlib.sha256(
                    f"legacy|{year}|{course}|{index}|{row.get('nota_final')}|{entry_vacancy}".encode("utf-8")
                ).hexdigest()
                records.append(
                    (
                        identity,
                        year,
                        course,
                        course,
                        float(row["nota_final"]),
                        entry_vacancy,
                        normalize_entry_mode(entry_vacancy),
                        row.get("situacao", ""),
                        collected_at,
                    )
                )

            connection.executemany(
                """
                INSERT OR IGNORE INTO candidate_current (
                    candidate_key, year, course, source_course, final_score,
                    entry_vacancy, entry_mode, status, collected_at, detailed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                """,
                records,
            )
            connection.execute(
                "INSERT INTO ranking_meta(key, value) VALUES ('legacy_imported', ?)",
                (collected_at,),
            )
            connection.commit()
            return len(records)

    def acquire_lock(self, owner: str, stale_after: timedelta = timedelta(hours=12)) -> bool:
        now = datetime.now(timezone.utc)
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            lock = connection.execute(
                "SELECT owner, acquired_at FROM sync_lock WHERE name = 'ranking-sync'"
            ).fetchone()
            if lock:
                acquired_at = datetime.fromisoformat(lock["acquired_at"])
                if now - acquired_at <= stale_after:
                    connection.rollback()
                    return False
                connection.execute("DELETE FROM sync_lock WHERE name = 'ranking-sync'")

            connection.execute(
                "INSERT INTO sync_lock(name, owner, acquired_at) VALUES ('ranking-sync', ?, ?)",
                (owner, now.isoformat(timespec="seconds")),
            )
            connection.commit()
            return True

    def release_lock(self, owner: str) -> None:
        with self.connect() as connection:
            connection.execute(
                "DELETE FROM sync_lock WHERE name = 'ranking-sync' AND owner = ?", (owner,)
            )
            connection.commit()

    def start_run(self, years: Iterable[int | str]) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO sync_run(started_at, status, years) VALUES (?, 'running', ?)",
                (utc_now(), json.dumps([int(year) for year in years])),
            )
            connection.commit()
            return int(cursor.lastrowid)

    def record_course_run(
        self, run_id: int, year: int, course: str, status: str, row_count: int = 0, error: str | None = None
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO sync_course_run(run_id, year, course, status, row_count, error, finished_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, year, course, status, row_count, error, utc_now()),
            )
            connection.commit()

    def finish_run(self, run_id: int, status: str, processed: int, failures: int, error: str | None = None) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE sync_run
                SET finished_at = ?, status = ?, courses_processed = ?, failures = ?, error_summary = ?
                WHERE id = ?
                """,
                (utc_now(), status, processed, failures, error, run_id),
            )
            connection.commit()

    def course_synced_today(self, year: int, course: str, local_date: str) -> bool:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM sync_course_run
                WHERE year = ? AND course = ? AND status = 'success' AND substr(finished_at, 1, 10) = ?
                LIMIT 1
                """,
                (year, course, local_date),
            ).fetchone()
            return row is not None

    def has_detailed_snapshot(self, year: int, course: str) -> bool:
        """Permite retomar um backfill sem confundir isso com a coleta diária."""
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT 1 FROM candidate_current
                WHERE year = ? AND course = ? AND detailed = 1
                LIMIT 1
                """,
                (year, course),
            ).fetchone()
            return row is not None

    def publish_course_snapshot(
        self,
        year: int,
        course: str,
        candidates: list[dict],
        *,
        force: bool = False,
        completeness_ratio: float = RANKING_MIN_COMPLETENESS_RATIO,
        collected_at: str | None = None,
    ) -> dict[str, int]:
        collected_at = collected_at or utc_now()
        self.validate_course_snapshot(
            year, course, candidates, force=force, completeness_ratio=completeness_ratio
        )
        keys = [candidate["candidate_key"] for candidate in candidates]

        inserted = updated = changed = inactivated = 0
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            previous_count = connection.execute(
                """
                SELECT COUNT(*) FROM candidate_current
                WHERE year = ? AND course = ? AND active = 1
                """,
                (year, course),
            ).fetchone()[0]
            existing_rows = connection.execute(
                "SELECT * FROM candidate_current WHERE year = ? AND course = ? AND detailed = 1",
                (year, course),
            ).fetchall()
            existing = {row["candidate_key"]: dict(row) for row in existing_rows}

            for candidate in candidates:
                current = existing.get(candidate["candidate_key"])
                values = {
                    "source_course": candidate.get("source_course", course),
                    "source_classification": candidate.get("source_classification"),
                    "name": candidate["name"],
                    "final_score": float(candidate["final_score"]),
                    "remapped_vacancy": candidate.get("remapped_vacancy"),
                    "competition_vacancies": candidate.get("competition_vacancies"),
                    "entry_vacancy": candidate["entry_vacancy"],
                    "entry_mode": candidate["entry_mode"],
                    "status": candidate["status"],
                    "status_date": candidate.get("status_date"),
                }

                if current:
                    changed_fields = [field for field in TRACKED_FIELDS if current.get(field) != values.get(field)]
                    if changed_fields:
                        before = {field: current.get(field) for field in changed_fields}
                        after = {field: values.get(field) for field in changed_fields}
                        connection.execute(
                            """
                            INSERT INTO candidate_change(
                                candidate_key, year, course, detected_at, changed_fields, before_json, after_json
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                candidate["candidate_key"], year, course, collected_at,
                                json.dumps(changed_fields), json.dumps(before, ensure_ascii=False),
                                json.dumps(after, ensure_ascii=False),
                            ),
                        )
                        changed += 1

                    connection.execute(
                        """
                        UPDATE candidate_current SET
                            source_course = ?, source_classification = ?, name = ?, final_score = ?,
                            remapped_vacancy = ?, competition_vacancies = ?, entry_vacancy = ?,
                            entry_mode = ?, status = ?, status_date = ?, collected_at = ?,
                            active = 1, missing_runs = 0, detailed = 1
                        WHERE candidate_key = ?
                        """,
                        (*values.values(), collected_at, candidate["candidate_key"]),
                    )
                    updated += 1
                else:
                    connection.execute(
                        """
                        INSERT INTO candidate_current(
                            candidate_key, year, course, source_course, source_classification, name,
                            final_score, remapped_vacancy, competition_vacancies, entry_vacancy,
                            entry_mode, status, status_date, collected_at, detailed
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                        """,
                        (
                            candidate["candidate_key"], year, course,
                            values["source_course"], values["source_classification"], values["name"],
                            values["final_score"], values["remapped_vacancy"], values["competition_vacancies"],
                            values["entry_vacancy"], values["entry_mode"], values["status"],
                            values["status_date"], collected_at,
                        ),
                    )
                    inserted += 1

            present = set(keys)
            for key, current in existing.items():
                if key in present:
                    continue
                missing_runs = current["missing_runs"] + 1
                active = 0 if missing_runs >= 2 else current["active"]
                if current["active"] and not active:
                    inactivated += 1
                connection.execute(
                    "UPDATE candidate_current SET missing_runs = ?, active = ? WHERE candidate_key = ?",
                    (missing_runs, active, key),
                )

            # O primeiro snapshot detalhado substitui o bootstrap anônimo do curso.
            connection.execute(
                "DELETE FROM candidate_current WHERE year = ? AND course = ? AND detailed = 0",
                (year, course),
            )
            connection.commit()

        return {"inserted": inserted, "updated": updated, "changed": changed, "inactivated": inactivated}

    def validate_course_snapshot(
        self,
        year: int,
        course: str,
        candidates: list[dict],
        *,
        force: bool = False,
        completeness_ratio: float = RANKING_MIN_COMPLETENESS_RATIO,
    ) -> None:
        if not candidates:
            raise ValueError(f"Snapshot vazio para {course} em {year}.")

        keys = [candidate.get("candidate_key") for candidate in candidates]
        if None in keys or len(keys) != len(set(keys)):
            raise ValueError(f"Snapshot possui candidatos sem chave ou duplicados para {course} em {year}.")

        required = {"candidate_key", "name", "final_score", "entry_vacancy", "entry_mode", "status"}
        for candidate in candidates:
            missing = required - set(candidate)
            empty = {field for field in required if candidate.get(field) in (None, "")}
            if missing or empty:
                raise ValueError(f"Candidato incompleto em {course}: {sorted(missing | empty)}.")

        with self.connect() as connection:
            previous_count = connection.execute(
                "SELECT COUNT(*) FROM candidate_current WHERE year = ? AND course = ? AND active = 1",
                (year, course),
            ).fetchone()[0]
        if previous_count and not force and len(candidates) < previous_count * completeness_ratio:
            raise ValueError(
                f"Snapshot de {course} tem {len(candidates)} registros; mínimo seguro: "
                f"{int(previous_count * completeness_ratio)}."
            )

    def get_cutoff(self, year: str | int, course: str, entry_mode: str) -> float:
        status_filters = " OR ".join("status LIKE ?" for _ in STATUS_PATTERNS)
        params = [int(year), course, entry_mode, *[f"%{value}%" for value in STATUS_PATTERNS]]
        with self.connect() as connection:
            row = connection.execute(
                f"""
                SELECT MIN(final_score) AS cutoff FROM candidate_current
                WHERE year = ? AND course = ? AND entry_mode = ? AND active = 1
                  AND ({status_filters})
                """,
                params,
            ).fetchone()
        if not row or row["cutoff"] is None:
            with self.connect() as connection:
                row = connection.execute(
                    """
                    SELECT cutoff FROM ranking_aggregate
                    WHERE year = ? AND course = ? AND entry_mode = ?
                    """,
                    (int(year), course, entry_mode),
                ).fetchone()
        if not row or row["cutoff"] is None:
            raise RuntimeError(f"Nenhuma nota de corte encontrada para {course} ({entry_mode}) em {year}.")
        return float(row["cutoff"])

    def cutoff_graph(self, reference_year: int, course: str, entry_mode: str, years_back: int = 5) -> dict[int, float]:
        graph = {}
        for year in range(max(2022, reference_year - years_back), reference_year + 1):
            try:
                graph[year] = self.get_cutoff(year, course, entry_mode)
            except RuntimeError:
                continue
        return graph

    def available_years(self, detailed_only: bool = False) -> list[str]:
        with self.connect() as connection:
            if detailed_only:
                rows = connection.execute(
                    "SELECT DISTINCT year FROM candidate_current WHERE detailed = 1 ORDER BY year DESC"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT year FROM candidate_current
                    UNION
                    SELECT year FROM ranking_aggregate
                    ORDER BY year DESC
                    """
                ).fetchall()
        return [str(row["year"]) for row in rows]

    def courses(self, year: str | int) -> list[str]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT course FROM candidate_current WHERE year = ?
                UNION
                SELECT course FROM ranking_aggregate WHERE year = ?
                ORDER BY course
                """,
                (int(year), int(year)),
            ).fetchall()
        return [row["course"] for row in rows]

    def candidate_window(
        self,
        year: int,
        course: str,
        *,
        entry_mode: str | None = None,
        anchor_score: float | None = None,
        offset: int | None = None,
        limit: int = 25,
    ) -> dict:
        filters = ["year = ?", "course = ?", "active = 1", "detailed = 1"]
        params: list = [year, course]
        if entry_mode:
            filters.append("entry_mode = ?")
            params.append(entry_mode)
        where = " AND ".join(filters)

        with self.connect() as connection:
            total = connection.execute(
                f"SELECT COUNT(*) FROM candidate_current WHERE {where}", params
            ).fetchone()[0]

            anchor_index = simulated_position = None
            if anchor_score is not None:
                # Empates existentes ficam antes da simulação: estimativa conservadora.
                anchor_index = connection.execute(
                    f"SELECT COUNT(*) FROM candidate_current WHERE {where} AND final_score >= ?",
                    [*params, anchor_score],
                ).fetchone()[0]
                simulated_position = anchor_index + 1

            if offset is None:
                offset = max(0, (anchor_index or 0) - limit // 2) if anchor_score is not None else 0
            offset = min(max(0, offset), max(0, total - limit))

            rows = connection.execute(
                f"""
                SELECT source_classification, name, final_score, remapped_vacancy,
                       competition_vacancies, entry_vacancy, entry_mode, status,
                       status_date, collected_at
                FROM candidate_current
                WHERE {where}
                ORDER BY final_score DESC,
                         CAST(COALESCE(source_classification, '999999999') AS INTEGER),
                         name COLLATE NOCASE
                LIMIT ? OFFSET ?
                """,
                [*params, limit, offset],
            ).fetchall()

            last_synced = connection.execute(
                f"SELECT MAX(collected_at) FROM candidate_current WHERE {where}", params
            ).fetchone()[0]

        items = []
        for index, row in enumerate(rows):
            item = dict(row)
            item["position"] = offset + index + 1
            items.append(item)
        is_stale = True
        if last_synced:
            is_stale = datetime.now(timezone.utc) - datetime.fromisoformat(last_synced) > timedelta(hours=36)
        return {
            "items": items,
            "total": total,
            "offset": offset,
            "limit": limit,
            "anchor_index": anchor_index,
            "simulated_position": simulated_position,
            "last_synced_at": last_synced,
            "is_stale": is_stale,
        }

    def status(self) -> dict:
        with self.connect() as connection:
            latest = connection.execute(
                "SELECT * FROM sync_run ORDER BY id DESC LIMIT 1"
            ).fetchone()
            success = connection.execute(
                "SELECT * FROM sync_run WHERE status = 'success' ORDER BY id DESC LIMIT 1"
            ).fetchone()
            latest_status_date = connection.execute(
                "SELECT MAX(status_date) FROM candidate_current WHERE detailed = 1"
            ).fetchone()[0]
        def with_duration(row):
            if not row:
                return None
            result = dict(row)
            if result["finished_at"]:
                started = datetime.fromisoformat(result["started_at"])
                finished = datetime.fromisoformat(result["finished_at"])
                result["duration_seconds"] = max(0, int((finished - started).total_seconds()))
            else:
                result["duration_seconds"] = None
            return result

        return {
            "last_run": with_duration(latest),
            "last_success": with_duration(success),
            "latest_source_status_date": latest_status_date,
        }

    def backup(self, backup_dir: str | Path, retention_days: int = 30) -> Path | None:
        if not self.path.exists():
            return None
        destination_dir = Path(backup_dir)
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"rankings-{datetime.now().strftime('%Y%m%d-%H%M%S')}.db"
        with self.connect() as source, sqlite3.connect(destination) as target:
            source.backup(target)

        cutoff = datetime.now() - timedelta(days=retention_days)
        for backup in destination_dir.glob("rankings-*.db"):
            if datetime.fromtimestamp(backup.stat().st_mtime) < cutoff:
                backup.unlink()
        return destination


repository = RankingRepository()
