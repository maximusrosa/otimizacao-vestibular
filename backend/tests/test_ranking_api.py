import pytest
from fastapi import HTTPException

from src import database
from src.main import get_ranking_candidates


def test_candidate_endpoint_contract(monkeypatch):
    expected = {
        "items": [],
        "total": 0,
        "offset": 0,
        "limit": 25,
        "anchor_index": 0,
        "simulated_position": 1,
        "last_synced_at": None,
        "is_stale": True,
    }
    monkeypatch.setattr(database, "get_candidate_window", lambda *args: expected)

    result = get_ranking_candidates(2025, "Curso", "LI_EP", 700.5, None, 25)
    assert result == expected


def test_candidate_endpoint_rejects_invalid_mode():
    with pytest.raises(HTTPException) as error:
        get_ranking_candidates(2025, "Curso", "INVALIDA", None, None, 25)
    assert error.value.status_code == 400
