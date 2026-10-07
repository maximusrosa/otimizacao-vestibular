import pytest

from src.ranking_scheduler import is_enabled, schedule_time
from src.sync_rankings import resolve_years


def test_scheduler_defaults_to_disabled(monkeypatch):
    monkeypatch.delenv("RANKING_SYNC_ENABLED", raising=False)
    assert is_enabled() is False


def test_scheduler_configuration(monkeypatch):
    monkeypatch.setenv("RANKING_SYNC_ENABLED", "true")
    monkeypatch.setenv("RANKING_SYNC_TIME", "05:00")
    assert is_enabled() is True
    assert schedule_time() == (5, 0)


def test_invalid_schedule_time_is_rejected(monkeypatch):
    monkeypatch.setenv("RANKING_SYNC_TIME", "25:00")
    with pytest.raises(RuntimeError):
        schedule_time()


def test_backfill_ends_at_largest_configured_year(monkeypatch):
    monkeypatch.setenv("RANKING_SYNC_YEARS", "2025")
    assert resolve_years(None, 2022) == [2022, 2023, 2024, 2025]


def test_detailed_collection_rejects_years_before_2022():
    with pytest.raises(ValueError, match="somente desde 2022"):
        resolve_years([2021], None)
