"""
Testes de integração — atingem o site real da UFRGS (rede) e/ou um browser real.

Desativados por padrão (ver `pytest.ini`). Para rodar:
    backend/.venv/bin/python -m pytest -m integration
"""
import os
import shutil
from pathlib import Path

import pytest

from src.constants import SUBJECTS, MIN_HITS, MAX_HITS, FOREIGN_LANGUAGES
from src.get_ranking import get_ranking, get_min_AC
from src.get_scores import get_scores
from src.optimization import optimization

EXPECTED_LEN = MAX_HITS - MIN_HITS + 1

LIVE_COURSE = "Ciência da Computação"
LIVE_YEAR = "2025"

_has_chrome = any(
    shutil.which(binary)
    for binary in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
)
requires_chrome = pytest.mark.skipif(
    not _has_chrome, reason="Chrome/Chromium não encontrado no PATH"
)


@pytest.fixture
def in_backend_dir():
    """
    optimization() lê data/course_weights.csv por caminho relativo ao cwd,
    que precisa ser a pasta backend/. Troca o cwd durante o teste e restaura.
    """
    original = Path.cwd()
    os.chdir(Path(__file__).resolve().parent.parent)  # .../backend
    try:
        yield
    finally:
        os.chdir(original)


@pytest.mark.integration
def test_get_scores_live_end_to_end():
    """Baixa a página real de histogramas e valida o dicionário completo."""
    scores = get_scores("2025", "Inglês")

    # Todas as disciplinas presentes
    assert set(scores.keys()) == set(SUBJECTS)

    for subject, values in scores.items():
        # 15 escores por disciplina, todos floats positivos
        assert len(values) == EXPECTED_LEN, subject
        assert all(isinstance(v, float) and v > 0 for v in values), subject
        # Escore padronizado é monotonicamente crescente com o nº de acertos
        assert values == sorted(values), subject

    # A língua estrangeira escolhida vira "LEM"
    assert scores["LEM"] != scores["MAT"]


@pytest.mark.integration
@pytest.mark.parametrize("language", FOREIGN_LANGUAGES)
def test_get_scores_live_all_languages(language):
    """Cada idioma disponível deve produzir um LEM válido de 15 escores."""
    scores = get_scores("2025", language)
    assert len(scores["LEM"]) == EXPECTED_LEN


@pytest.mark.integration
@requires_chrome
def test_get_ranking_live_end_to_end():
    """
    Dirige o Chrome real pelo site de chamamento (Selenium) e valida o
    ranking extraído + o cálculo da nota de corte.
    """
    ranking = get_ranking(LIVE_YEAR, LIVE_COURSE)

    assert len(ranking) > 0
    # Cada candidato tem ao menos as colunas lidas por get_min_AC (Média, Vaga, Situação)
    assert all(len(candidate) >= 8 for candidate in ranking)

    # A nota de corte da ampla concorrência deve ser um float plausível
    min_ac = get_min_AC(ranking, "AC")
    assert isinstance(min_ac, float)
    assert 0 < min_ac < 1000


@pytest.mark.integration
@requires_chrome
def test_optimize_full_pipeline_live(in_backend_dir):
    """
    Fluxo completo do endpoint /optimize (sem HTTP), com dados reais:
    get_scores + get_ranking/get_min_AC -> optimization.
    """
    std_scores = get_scores("2025", "Inglês")
    ranking = get_ranking(LIVE_YEAR, LIVE_COURSE)
    min_AC = get_min_AC(ranking, "AC")

    result = optimization(LIVE_COURSE, min_AC, std_scores, {}, SUBJECTS)

    assert result.solve_status == "Optimal"
    assert result.threshold == min_AC
    # A nota alcançada deve satisfazer o limite mínimo (com folga numérica)
    assert result.AC >= min_AC - 1e-2
    # Uma escolha de acertos válida para cada disciplina
    assert set(result.chosen_hits.keys()) == set(SUBJECTS)
    for subject, info in result.chosen_hits.items():
        assert MIN_HITS <= info["num_hits"] <= MAX_HITS, subject
        assert info["EP"] > 0, subject

