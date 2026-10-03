import os
import ssl
from functools import lru_cache
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .constants import (
    FOREIGN_LANGUAGES,
    MAX_HITS,
    MIN_HITS,
    SCORES_URL,
    SUBJECT_NAME_TO_CODE,
    SUBJECTS,
)


def _ca_bundle() -> str | bool:
    """Return configured or operating-system CA bundle."""
    configured_bundle = os.environ.get("REQUESTS_CA_BUNDLE")
    if configured_bundle:
        return configured_bundle

    system_bundle = ssl.get_default_verify_paths().cafile
    if system_bundle and Path(system_bundle).is_file():
        return system_bundle

    return True


def _retrying_session() -> requests.Session:
    """Cria uma sessão que tolera falhas transitórias da UFRGS."""
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        status=5,
        other=5,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
    )
    session = requests.Session()
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


@lru_cache(maxsize=8)
def _download_scores_html(year: str) -> str:
    """Baixa e guarda HTML estático para reduzir dependência da UFRGS."""
    with _retrying_session() as session:
        response = session.get(
            SCORES_URL.format(year=year),
            timeout=(10, 30),
            verify=_ca_bundle(),
        )
    response.raise_for_status()
    return response.text


def _parse_float(text: str) -> float:
    """Converte número em formato brasileiro ('1.234,56') para float."""
    text = text.strip()
    text = text.replace(",", ".")
    # Se houver mais de um ponto, removemos o primeiro (que é o separador de milhar)
    if text.count(".") > 1:
        text = text.replace(".", "", 1)
    return float(text)


def _parse_std_scores(table) -> dict[int, float]:
    """Extrai {escore: escore_padronizado} de uma tabela de histograma."""
    tbody = table.find("tbody")
    if not tbody:
        return {}

    scores = {}
    for tr in tbody.find_all("tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) < 2:
            continue
        hits = int(cols[0])                   # Escore (número de acertos)
        scores[hits] = _parse_float(cols[1])  # Escore padronizado
    return scores


def parse_scores(html: str, foreign_language: str) -> dict[str, list[float]]:
    """
    Extrai os escores padronizados por acerto (MIN_HITS..MAX_HITS) de cada
    disciplina a partir do HTML da página de histogramas da UFRGS.

    Retorna um dicionário {código_disciplina: [escores padronizados]}, onde a
    língua estrangeira escolhida (`foreign_language`) é mapeada para "LEM".
    """
    if foreign_language not in FOREIGN_LANGUAGES:
        raise ValueError(
            f"Língua estrangeira inválida: {foreign_language}. "
            f"Opções: {FOREIGN_LANGUAGES}"
        )

    soup = BeautifulSoup(html, "html.parser")

    rows = soup.find_all("div", class_="row")

    std_scores: dict[str, list[float]] = {}

    for row in rows:
        # As duas colunas dentro da linha (tabela de dados + cabeçalho)
        cols = row.select("div.col.s12.m6")
        if len(cols) < 2:
            continue

        table_heading = cols[1].select_one("table.col.s12")
        if not table_heading:
            continue

        th = table_heading.select_one("thead tr th[colspan='2']")
        if not th:
            continue

        subject = th.get_text(strip=True)

        # Mapeia o nome da disciplina para o código interno
        if subject in SUBJECT_NAME_TO_CODE:
            code = SUBJECT_NAME_TO_CODE[subject]
        elif subject == foreign_language:
            code = "LEM"
        else:
            continue  # Ignora línguas não escolhidas e tabelas irrelevantes

        if code in std_scores:
            continue  # Evita duplicatas (ex.: "Língua Portuguesa" aparece 2x)

        table = cols[0].select_one("table.col.s12")
        if not table:
            continue

        scores = _parse_std_scores(table)

        # Seleciona os escores de MIN_HITS a MAX_HITS (descarta o escore 0)
        std_scores[code] = [scores[hits] for hits in range(MIN_HITS, MAX_HITS + 1)]

    missing = [s for s in SUBJECTS if s not in std_scores]
    if missing:
        raise RuntimeError(f"Escores não encontrados para as disciplinas: {missing}")

    return std_scores


def get_scores(year: str, foreign_language: str) -> dict[str, list[float]]:
    """Baixa a página de histogramas do ano e extrai os escores padronizados."""
    return parse_scores(_download_scores_html(year), foreign_language)


def main():
    year = "2025"
    foreign_language = "Alemão"

    std_scores = get_scores(year, foreign_language)

    for subject, scores in std_scores.items():
        print(f"{subject:9s} -> {scores}")


if __name__ == "__main__":
    main()
