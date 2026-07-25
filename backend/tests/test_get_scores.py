import pytest
import responses

from src.constants import SUBJECTS, MIN_HITS, MAX_HITS, SCORES_URL
from src.get_scores import _parse_float, parse_scores, get_scores

EXPECTED_LEN = MAX_HITS - MIN_HITS + 1  # 15 escores por disciplina

# ---------- parse_scores (contra fixture real) ----------
def test_parse_scores_returns_all_subjects(scores_html):
    scores = parse_scores(scores_html, "Inglês")
    assert set(scores.keys()) == set(SUBJECTS)


def test_parse_scores_each_subject_has_15_values(scores_html):
    scores = parse_scores(scores_html, "Inglês")
    for subject, values in scores.items():
        assert len(values) == EXPECTED_LEN, subject
        assert all(isinstance(v, float) for v in values)


def test_parse_scores_known_values(scores_html):
    # Valores conferidos na página cv2025 (índice 0 = 1 acerto).
    scores = parse_scores(scores_html, "Inglês")
    assert scores["MAT"][0] == 353.10   # 1 acerto
    assert scores["MAT"][-1] == 774.52  # 15 acertos
    assert scores["PORT_RED"][0] == 245.02


def test_parse_scores_maps_chosen_language_to_lem(scores_html):
    ingles = parse_scores(scores_html, "Inglês")["LEM"]
    espanhol = parse_scores(scores_html, "Espanhol")["LEM"]
    assert ingles[0] == 301.00
    assert espanhol[0] == 296.48
    assert ingles != espanhol


def test_parse_scores_invalid_language_raises(scores_html):
    with pytest.raises(ValueError):
        parse_scores(scores_html, "Klingon")


def test_parse_scores_missing_subject_raises():
    with pytest.raises(RuntimeError):
        parse_scores("<html><body></body></html>", "Inglês")


# ---------- get_scores (I/O mockada) ----------
@responses.activate
def test_get_scores_fetches_year_url(scores_html):
    year = "2025"
    responses.add(responses.GET, SCORES_URL.format(year=year),
                  body=scores_html, status=200)

    scores = get_scores(year, "Inglês")

    assert set(scores.keys()) == set(SUBJECTS)
    assert responses.calls[0].request.url == SCORES_URL.format(year=year)
