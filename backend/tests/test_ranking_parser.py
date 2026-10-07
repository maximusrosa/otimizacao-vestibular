import pytest

from src.save_rankings import parse_candidate_table


def test_parser_uses_headers_instead_of_fixed_positions(ranking_detailed_html):
    candidates = parse_candidate_table(
        ranking_detailed_html,
        2025,
        "Ciência da Computação - Bacharelado",
        "Ciência da Computação",
    )

    assert len(candidates) == 2
    assert candidates[0]["name"] == "Fulano da Silva"
    assert candidates[0]["final_score"] == 780.5
    assert candidates[0]["remapped_vacancy"] == "2025/1"
    assert candidates[0]["competition_vacancies"] == "LI_EP"
    assert candidates[0]["entry_mode"] == "LI_EP"
    assert candidates[0]["status_date"] == "2025-03-15"
    assert "1001" not in candidates[0]["candidate_key"]
    assert candidates[1]["status_date"] is None


def test_parser_rejects_missing_required_header(ranking_detailed_html):
    html = ranking_detailed_html.replace("<th>Data da situação</th>", "")
    with pytest.raises(RuntimeError, match="status_date"):
        parse_candidate_table(html, 2025, "Curso")


def test_parser_rejects_invalid_status_date(ranking_detailed_html):
    html = ranking_detailed_html.replace("15/03/2025", "ontem")
    with pytest.raises(ValueError, match="Data de situação inválida"):
        parse_candidate_table(html, 2025, "Curso")
