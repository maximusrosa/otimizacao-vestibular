"""CLI idempotente para sincronizar candidatos e situações da UFRGS."""

from __future__ import annotations

import argparse
import os
import socket
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from selenium.webdriver.support.ui import WebDriverWait

from .constants import (
    DATA_DIR,
    RANKING_DB_PATH,
    RANKING_MIN_COMPLETENESS_RATIO,
    RANKING_MIN_DETAIL_YEAR,
)
from .ranking_repository import RankingRepository
from .save_rankings import create_driver, fetch_course_candidates, select_year_and_exam
from .utils import COURSE_MAPPING


def configured_years() -> list[int]:
    value = os.environ.get("RANKING_SYNC_YEARS", "2025")
    return sorted({int(year.strip()) for year in value.split(",") if year.strip()})


def resolve_years(explicit_years: list[int] | None, from_year: int | None) -> list[int]:
    years = explicit_years or configured_years()
    if from_year is not None:
        last_year = max(years)
        years = list(range(from_year, last_year + 1))
    years = sorted(set(years))
    invalid = [year for year in years if year < RANKING_MIN_DETAIL_YEAR]
    if invalid:
        raise ValueError(f"Rankings detalhados são mantidos somente desde {RANKING_MIN_DETAIL_YEAR}.")
    return years


def sync_rankings(
    years: list[int],
    *,
    dry_run: bool = False,
    resume: bool = False,
    backfill: bool = False,
    force: bool = False,
    repository: RankingRepository | None = None,
) -> dict:
    repository = repository or RankingRepository(RANKING_DB_PATH)
    repository.initialize(DATA_DIR / "rankings_completos.json")

    owner = f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:8]}"
    if not repository.acquire_lock(owner):
        raise RuntimeError("Já existe uma sincronização de rankings em execução.")

    run_id = None
    processed = failures = skipped = 0
    failure_messages = []
    driver = None
    try:
        run_id = repository.start_run(years)
        if not dry_run:
            repository.backup(repository.path.parent / "backups", retention_days=30)
        for year in years:
            driver = create_driver()
            try:
                source_courses = select_year_and_exam(driver, WebDriverWait(driver, 15), year)
                for source_course in source_courses:
                    course = COURSE_MAPPING.get(source_course, source_course)
                    local_timezone = ZoneInfo(os.environ.get("TZ", "America/Sao_Paulo"))
                    local_date = datetime.now(local_timezone).date().isoformat()
                    already_published = backfill and repository.has_detailed_snapshot(year, course)
                    if resume and (already_published or repository.course_synced_today(year, course, local_date)):
                        skipped += 1
                        continue

                    print(f"[{year}] Sincronizando {course}...")
                    try:
                        canonical_course, candidates = fetch_course_candidates(driver, year, source_course)
                        repository.validate_course_snapshot(
                            year,
                            canonical_course,
                            candidates,
                            force=force,
                            completeness_ratio=RANKING_MIN_COMPLETENESS_RATIO,
                        )
                        if not dry_run:
                            repository.publish_course_snapshot(
                                year,
                                canonical_course,
                                candidates,
                                force=force,
                                completeness_ratio=RANKING_MIN_COMPLETENESS_RATIO,
                            )
                        course_status = "validated" if dry_run else "success"
                        repository.record_course_run(run_id, year, canonical_course, course_status, len(candidates))
                        processed += 1
                    except Exception as error:
                        failures += 1
                        message = f"{year}/{course}: {error}"
                        failure_messages.append(message)
                        repository.record_course_run(run_id, year, course, "failed", error=str(error))
                        print(f"[ERRO] {message}")
                    time.sleep(1.5)
            finally:
                driver.quit()
                driver = None

        status = "dry_run" if dry_run and failures == 0 else "success" if failures == 0 else "partial"
        repository.finish_run(run_id, status, processed, failures, "\n".join(failure_messages) or None)
        return {"status": status, "processed": processed, "failures": failures, "skipped": skipped}
    except Exception as error:
        if run_id is not None:
            repository.finish_run(run_id, "failed", processed, failures + 1, str(error))
        raise
    finally:
        if driver is not None:
            driver.quit()
        repository.release_lock(owner)


def main():
    parser = argparse.ArgumentParser(description="Sincroniza rankings e situações publicados pela UFRGS.")
    parser.add_argument("--year", type=int, action="append", dest="years", help="Ano a sincronizar; pode ser repetido.")
    parser.add_argument("--from-year", type=int, help="Executa backfill deste ano até o maior ano configurado.")
    parser.add_argument("--dry-run", action="store_true", help="Coleta e valida sem publicar candidatos.")
    parser.add_argument("--resume", action="store_true", help="Pula cursos já concluídos no dia atual.")
    parser.add_argument("--force", action="store_true", help="Ignora a proteção de queda abrupta no total de candidatos.")
    args = parser.parse_args()

    years = resolve_years(args.years, args.from_year)
    result = sync_rankings(
        years,
        dry_run=args.dry_run,
        resume=args.resume,
        backfill=args.from_year is not None,
        force=args.force,
    )
    print(result)


if __name__ == "__main__":
    main()
