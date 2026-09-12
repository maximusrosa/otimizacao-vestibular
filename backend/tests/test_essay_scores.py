import pytest

from src.essay_scores import (
    calculate_essay_standard_score,
    compose_port_red_score,
    compose_port_red_scores,
    parse_decimal,
    parse_essay_stats,
    parse_integer,
)


def test_parse_decimal_accepts_brazilian_and_dot_formats():
    assert parse_decimal("9,9959") == 9.9959
    assert parse_decimal("2.3280") == 2.328
    assert parse_decimal(" 14,9769 ") == 14.9769


def test_parse_integer_accepts_thousands_separator():
    assert parse_integer("7.933") == 7933
    assert parse_integer("14.525") == 14525
    assert parse_integer("-") is None


def test_parse_essay_stats_extracts_valid_years(essay_stats_html):
    stats = parse_essay_stats(essay_stats_html)

    assert stats["2025"]["mean"] == 9.9959
    assert stats["2025"]["std_dev"] == 2.328
    assert stats["2025"]["corrected_count"] == 7933
    assert stats["2025"]["corrected_percentage"] == 43.30
    assert "2006" not in stats


def test_calculate_essay_standard_score():
    score = calculate_essay_standard_score(raw_score=12.0, mean=10.0, std_dev=2.0)

    assert score == 600.0


def test_calculate_essay_standard_score_validates_range():
    with pytest.raises(ValueError):
        calculate_essay_standard_score(raw_score=15.5, mean=10.0, std_dev=2.0)


def test_compose_port_red_score_uses_simple_average():
    assert compose_port_red_score(700.0, 500.0) == 600.0
    assert compose_port_red_scores([400.0, 600.0], 500.0) == [450.0, 550.0]
