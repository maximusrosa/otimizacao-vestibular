import pytest

from src.scripts.update_year_data import (
    records_to_nested_scores,
    validate_essay_for_year,
    validate_rankings_for_year,
    validate_scores_for_year,
)


def test_records_to_nested_scores_groups_by_discipline_and_hits():
    records = [
        {"ano": 2025, "disciplina": "MAT", "acertos": 1, "escore": 353.1},
        {"ano": 2025, "disciplina": "MAT", "acertos": 2, "escore": 383.2},
    ]

    assert records_to_nested_scores(records) == {"MAT": {"1": 353.1, "2": 383.2}}


def test_validate_essay_for_year_rejects_missing_year():
    with pytest.raises(RuntimeError):
        validate_essay_for_year("2026", {"2025": {"mean": 9.99, "std_dev": 2.3}})


def test_validate_rankings_for_year_rejects_empty_data():
    with pytest.raises(RuntimeError):
        validate_rankings_for_year("2025", [])


def test_validate_scores_for_year_rejects_incomplete_subjects():
    with pytest.raises(RuntimeError):
        validate_scores_for_year("2025", {"MAT": {"1": 353.1}})
