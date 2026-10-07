import json
import sqlite3

import pytest

from src.ranking_repository import RankingRepository, candidate_key


def make_candidate(index: int, *, score=None, status="Matriculado"):
    return {
        "candidate_key": candidate_key(2025, "Curso", str(1000 + index)),
        "source_course": "Curso do site",
        "source_classification": str(index),
        "name": f"Candidato {index}",
        "final_score": score if score is not None else 800 - index * 10,
        "remapped_vacancy": None,
        "competition_vacancies": "LI_EP",
        "entry_vacancy": "LI_EP",
        "entry_mode": "LI_EP",
        "status": status,
        "status_date": "2025-03-15",
    }


@pytest.fixture
def repository(tmp_path):
    value = RankingRepository(tmp_path / "rankings.db")
    value.initialize()
    return value


def test_publish_query_and_center_window(repository):
    candidates = [make_candidate(index) for index in range(1, 31)]
    repository.publish_course_snapshot(2025, "Curso", candidates)

    window = repository.candidate_window(
        2025, "Curso", entry_mode="LI_EP", anchor_score=650, limit=5
    )

    assert window["total"] == 30
    assert window["simulated_position"] == 16
    assert window["offset"] == 13
    assert len(window["items"]) == 5
    assert repository.get_cutoff(2025, "Curso", "LI_EP") == 500


def test_history_is_written_only_when_tracked_data_changes(repository):
    candidate = make_candidate(1)
    repository.publish_course_snapshot(2025, "Curso", [candidate])
    repository.publish_course_snapshot(2025, "Curso", [candidate])

    changed = {**candidate, "status": "Renunciante", "status_date": "2025-03-16"}
    repository.publish_course_snapshot(2025, "Curso", [changed])

    with repository.connect() as connection:
        rows = connection.execute("SELECT * FROM candidate_change").fetchall()
    assert len(rows) == 1
    assert set(json.loads(rows[0]["changed_fields"])) == {"status", "status_date"}


def test_status_change_updates_cutoff_without_repository_reload(repository):
    high_score = make_candidate(1, score=700)
    low_score = make_candidate(2, score=600)
    repository.publish_course_snapshot(2025, "Curso", [high_score, low_score])
    assert repository.get_cutoff(2025, "Curso", "LI_EP") == 600

    eliminated = {**low_score, "status": "Eliminado", "status_date": "2025-03-16"}
    repository.publish_course_snapshot(2025, "Curso", [high_score, eliminated])

    assert repository.get_cutoff(2025, "Curso", "LI_EP") == 700


def test_candidate_is_inactivated_only_after_two_complete_absences(repository):
    candidates = [make_candidate(index) for index in range(1, 6)]
    repository.publish_course_snapshot(2025, "Curso", candidates)
    remaining = candidates[:-1]

    repository.publish_course_snapshot(2025, "Curso", remaining)
    assert repository.candidate_window(2025, "Curso", limit=10)["total"] == 5
    repository.publish_course_snapshot(2025, "Curso", remaining)
    assert repository.candidate_window(2025, "Curso", limit=10)["total"] == 4


def test_incomplete_snapshot_is_rejected_without_partial_write(repository):
    candidates = [make_candidate(index) for index in range(1, 6)]
    repository.publish_course_snapshot(2025, "Curso", candidates)

    with pytest.raises(ValueError, match="mínimo seguro"):
        repository.publish_course_snapshot(2025, "Curso", candidates[:2])
    assert repository.candidate_window(2025, "Curso", limit=10)["total"] == 5


def test_sync_lock_is_exclusive_and_releasable(repository):
    assert repository.acquire_lock("first") is True
    assert repository.acquire_lock("second") is False
    repository.release_lock("first")
    assert repository.acquire_lock("second") is True


def test_legacy_import_is_anonymous_and_runs_once(tmp_path):
    legacy = tmp_path / "legacy.json"
    legacy.write_text(json.dumps([{
        "ano": 2020,
        "curso": "Curso",
        "nota_final": 700.0,
        "modalidade": "AC",
        "situacao": "Matriculado",
    }]), encoding="utf-8")
    repository = RankingRepository(tmp_path / "rankings.db")

    repository.initialize(legacy)

    assert repository.import_legacy_json_once(legacy) == 0
    with repository.connect() as connection:
        candidate_count = connection.execute("SELECT COUNT(*) FROM candidate_current").fetchone()[0]
        aggregate = connection.execute("SELECT * FROM ranking_aggregate").fetchone()
    assert candidate_count == 0
    assert aggregate["cutoff"] == 700
    assert repository.get_cutoff(2020, "Curso", "AC") == 700


def test_detailed_snapshot_replaces_post_2022_anonymous_bootstrap(tmp_path):
    legacy = tmp_path / "legacy.json"
    legacy.write_text(json.dumps([{
        "ano": 2025,
        "curso": "Curso",
        "nota_final": 700.0,
        "modalidade": "LI_EP",
        "situacao": "Matriculado",
    }]), encoding="utf-8")
    repository = RankingRepository(tmp_path / "rankings.db")
    repository.initialize(legacy)

    with repository.connect() as connection:
        bootstrap = connection.execute(
            "SELECT name, detailed FROM candidate_current"
        ).fetchone()
    assert bootstrap["name"] is None
    assert bootstrap["detailed"] == 0

    repository.publish_course_snapshot(2025, "Curso", [make_candidate(1)])
    with repository.connect() as connection:
        rows = connection.execute(
            "SELECT name, detailed FROM candidate_current WHERE year = 2025 AND course = 'Curso'"
        ).fetchall()
    assert [(row["name"], row["detailed"]) for row in rows] == [("Candidato 1", 1)]
