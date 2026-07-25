import pytest

from src.get_ranking import parse_ranking, get_min_AC


# ---------- parse_ranking ----------
def test_parse_ranking_extracts_rows(ranking_html):
    ranking = parse_ranking(ranking_html)
    assert len(ranking) == 6           # cabeçalho descartado
    assert ranking[0][2] == "Fulano"   # coluna Nome
    assert ranking[0][6] == "AC"       # Vaga de ingresso


def test_parse_ranking_missing_table_raises():
    with pytest.raises(RuntimeError):
        parse_ranking("<html><body><p>sem tabela</p></body></html>")


# ---------- get_min_AC ----------
def test_get_min_AC_returns_lowest_matriculado(ranking_html):
    ranking = parse_ranking(ranking_html)
    # LI_EP: 770 (Matriculado), 760 (Lotado), 750 e 740 (Renunciante) contam;
    # o mínimo entre os que contam é 740.
    assert get_min_AC(ranking, "LI_EP") == 740.0


def test_get_min_AC_ac_single_candidate(ranking_html):
    ranking = parse_ranking(ranking_html)
    assert get_min_AC(ranking, "AC") == 780.5


def test_get_min_AC_ignores_invalid_status():
    # Único candidato LI_EP tem status que não conta -> sem nota.
    ranking = [["1", "1", "X", "700.0", "700.0", "1", "LI_EP", "Não comparecente"]]
    with pytest.raises(RuntimeError):
        get_min_AC(ranking, "LI_EP")


def test_get_min_AC_no_match_raises(ranking_html):
    ranking = parse_ranking(ranking_html)
    with pytest.raises(RuntimeError):
        get_min_AC(ranking, "LB_Q")
