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
    """Usa o bundle configurado, o do sistema ou o padrão do requests."""
    configured_bundle = os.environ.get("REQUESTS_CA_BUNDLE")
    if configured_bundle:
        return configured_bundle
    system_bundle = ssl.get_default_verify_paths().cafile
    if system_bundle and Path(system_bundle).is_file():
        return system_bundle
    return True


def _retrying_session() -> requests.Session:
    """Cria uma sessão tolerante a falhas transitórias da página da UFRGS."""
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
    """Baixa e memoriza o HTML para evitar requisições repetidas no mesmo processo."""
    with _retrying_session() as session:
        response = session.get(
            SCORES_URL.format(year=year),
            timeout=(10, 30),
            verify=_ca_bundle(),
        )
    response.raise_for_status()
    return response.text


def _parse_float(text: str) -> float:
    """Converte números com separadores brasileiros ou internacionais."""
    text = text.strip()
    last_separator = max(text.rfind("."), text.rfind(","))
    if last_separator == -1:
        return float(text)
    integer = text[:last_separator].replace(".", "").replace(",", "")
    fraction = text[last_separator + 1 :]
    return float(f"{integer}.{fraction}")


def _parse_std_scores(table) -> dict[int, float]:
    tbody = table.find("tbody")
    if not tbody:
        return {}

    scores = {}
    for row in tbody.find_all("tr"):
        columns = [cell.get_text(strip=True) for cell in row.find_all("td")]
        if len(columns) >= 2:
            scores[int(columns[0])] = _parse_float(columns[1])
    return scores


def parse_scores(html: str, foreign_language: str) -> dict[str, list[float]]:
    """Extrai os EPs das nove provas objetivas para a língua escolhida."""
    if foreign_language not in FOREIGN_LANGUAGES:
        raise ValueError(f"Língua estrangeira inválida: {foreign_language}.")

    soup = BeautifulSoup(html, "html.parser")
    std_scores: dict[str, list[float]] = {}

    for row in soup.find_all("div", class_="row"):
        columns = row.select("div.col.s12.m6")
        if len(columns) < 2:
            continue

        heading = columns[1].select_one("table.col.s12 thead tr th[colspan='2']")
        table = columns[0].select_one("table.col.s12")
        if not heading or not table:
            continue

        subject_name = heading.get_text(strip=True)
        if subject_name in SUBJECT_NAME_TO_CODE:
            code = SUBJECT_NAME_TO_CODE[subject_name]
        elif subject_name == foreign_language:
            code = "LEM"
        else:
            continue

        if code in std_scores:
            continue

        scores = _parse_std_scores(table)
        try:
            std_scores[code] = [scores[hits] for hits in range(MIN_HITS, MAX_HITS + 1)]
        except KeyError as error:
            raise RuntimeError(f"Escore ausente para {code}: {error.args[0]} acertos.") from error

    missing = set(SUBJECTS) - set(std_scores)
    if missing:
        raise RuntimeError(f"Escores não encontrados para as disciplinas: {sorted(missing)}.")
    return std_scores


def get_scores(year: str, foreign_language: str) -> dict[str, list[float]]:
    return parse_scores(_download_scores_html(year), foreign_language)
