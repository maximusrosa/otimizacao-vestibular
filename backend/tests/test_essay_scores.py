import pytest

from src.essay_scores import (
    build_essay_score_options,
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


def test_build_essay_score_options_uses_tenths_inside_constraints():
    options = build_essay_score_options(4.56, 4.81, mean=10.0, std_dev=2.0)

    assert [option["raw_score"] for option in options] == [4.6, 4.7, 4.8]
    assert options[0]["standard_score"] == 230.0


def test_build_essay_score_options_never_goes_below_elimination_score():
    options = build_essay_score_options(0.0, 4.6, mean=10.0, std_dev=2.0)

    assert [option["raw_score"] for option in options] == [4.5, 4.6]
