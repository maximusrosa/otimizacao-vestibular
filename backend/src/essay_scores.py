"""Leitura, padronizacao e persistencia das notas de redacao."""

import csv
import json
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .constants import (
    ESSAY_SCORE_STEP,
    ESSAY_STATS_URL,
    MAX_ESSAY_SCORE,
    MIN_APPROVED_ESSAY_SCORE,
    MIN_ESSAY_SCORE,
)


def parse_decimal(text: str) -> float:
    """Converte numeros nos formatos brasileiro e internacional para float."""
    value = text.strip().replace("\xa0", "")
    if not value or value == "-":
        raise ValueError("valor decimal ausente")

    last_sep = max(value.rfind("."), value.rfind(","))
    if last_sep == -1:
        return float(value)

    integer = value[:last_sep].replace(".", "").replace(",", "")
    fraction = value[last_sep + 1 :]
    return float(f"{integer}.{fraction}")


def parse_integer(text: str) -> int | None:
    """Converte contagens com separador de milhar; '-' representa dado ausente."""
    value = text.strip().replace("\xa0", "")
    if not value or value == "-":
        return None
    return int(value.replace(".", "").replace(",", ""))


def parse_optional_decimal(text: str) -> float | None:
    """Converte um decimal opcional, inclusive percentuais sem alterar a escala."""
    value = text.strip().replace("\xa0", "").replace("%", "")
    if not value or value == "-":
        return None
    return parse_decimal(value)


def parse_essay_stats(html: str) -> dict[str, dict[str, float | int | None]]:
    """Extrai media, desvio e quantidade de redacoes de cada ano disponivel."""
    soup = BeautifulSoup(html, "html.parser")
    if soup.find("table") is None:
        raise RuntimeError("Tabela de estatísticas da redação não encontrada.")

    stats = {}
    # A pagina possui uma tabela de titulo antes da tabela de dados. Percorrer
    # todas as linhas torna o parser independente da posicao da tabela anual.
    for row in soup.find_all("tr"):
        cols = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
        if len(cols) < 3 or not cols[0].isdigit():
            continue

        year = cols[0]
        try:
            mean = parse_decimal(cols[1])
            std_dev = parse_decimal(cols[2])
        except ValueError:
            continue

        stats[year] = {
            "mean": mean,
            "std_dev": std_dev,
            "corrected_count": parse_integer(cols[3]) if len(cols) > 3 else None,
            "corrected_percentage": parse_optional_decimal(cols[4]) if len(cols) > 4 else None,
        }

    if not stats:
        raise RuntimeError("Nenhuma estatística de redação válida foi encontrada.")

    return stats


def fetch_essay_stats(url: str = ESSAY_STATS_URL) -> dict[str, dict[str, float | int | None]]:
    """Baixa e interpreta a serie historica de estatisticas da redacao."""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return parse_essay_stats(response.text)


def calculate_essay_standard_score(raw_score: float, mean: float, std_dev: float) -> float:
    """Calcula EP = 500 + 100 * (nota - media) / desvio_padrao."""
    if not MIN_ESSAY_SCORE <= raw_score <= MAX_ESSAY_SCORE:
        raise ValueError(f"Nota da redação deve estar entre {MIN_ESSAY_SCORE:g} e {MAX_ESSAY_SCORE:g}.")
    if std_dev <= 0:
        raise ValueError("Desvio padrão da redação deve ser maior que zero.")

    return 500 + 100 * ((raw_score - mean) / std_dev)


def compose_port_red_score(portuguese_ep: float, essay_ep: float) -> float:
    """Combina Portugues e Redacao, cada parte com peso de 50%."""
    return (portuguese_ep + essay_ep) / 2


def compose_port_red_scores(portuguese_scores: list[float], essay_ep: float) -> list[float]:
    """Aplica a composicao 50/50 a cada alternativa de acertos em Portugues."""
    return [compose_port_red_score(portuguese_ep, essay_ep) for portuguese_ep in portuguese_scores]


def build_essay_score_options(
    minimum: float,
    maximum: float,
    mean: float,
    std_dev: float,
    step: float = ESSAY_SCORE_STEP,
) -> list[dict[str, float]]:
    """Cria a grade decimal de notas que sera oferecida ao solver."""
    if minimum > maximum:
        raise ValueError("Nota mínima da redação não pode superar a máxima.")
    if step <= 0:
        raise ValueError("Passo da nota da redação deve ser maior que zero.")

    # Decimal evita que a grade 4.5, 4.6, ... acumule erros binarios de float.
    step_decimal = Decimal(str(step))
    minimum_decimal = max(Decimal(str(minimum)), Decimal(str(MIN_APPROVED_ESSAY_SCORE)))
    maximum_decimal = min(Decimal(str(maximum)), Decimal(str(MAX_ESSAY_SCORE)))
    first_index = (minimum_decimal / step_decimal).to_integral_value(rounding=ROUND_CEILING)
    last_index = (maximum_decimal / step_decimal).to_integral_value(rounding=ROUND_FLOOR)

    options = []
    for index in range(int(first_index), int(last_index) + 1):
        raw_score = float(Decimal(index) * step_decimal)
        options.append(
            {
                "raw_score": raw_score,
                "standard_score": calculate_essay_standard_score(raw_score, mean, std_dev),
            }
        )

    if not options:
        raise ValueError("Nenhuma nota de redação da grade de 0,1 cabe nos limites informados.")
    return options


def save_essay_stats_to_json(stats: dict[str, dict], filename: str | Path = "data/redacao_stats.json"):
    """Salva a estrutura otimizada para leitura da API."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def save_essay_stats_to_csv(stats: dict[str, dict], filename: str | Path = "data/redacao_stats.csv"):
    """Salva uma copia tabular das estatisticas para auditoria manual."""
    fieldnames = ["year", "mean", "std_dev", "corrected_count", "corrected_percentage"]
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for year in sorted(stats, key=int):
            row = {"year": year, **stats[year]}
            writer.writerow(row)


def main():
    stats = fetch_essay_stats()
    save_essay_stats_to_json(stats)
    save_essay_stats_to_csv(stats)
    print(f"Estatísticas de redação salvas para {len(stats)} anos.")


if __name__ == "__main__":
    main()
