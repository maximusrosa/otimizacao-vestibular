from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def scores_html() -> str:
    """HTML real da página de histogramas da UFRGS (cv2025)."""
    return (FIXTURES_DIR / "histogramas_2025.html").read_text(encoding="utf-8")


@pytest.fixture
def ranking_html() -> str:
    """HTML sintético com a tabela de ranking de chamamento."""
    return (FIXTURES_DIR / "ranking_sample.html").read_text(encoding="utf-8")
