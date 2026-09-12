import csv
import json
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from .constants import ESSAY_STATS_URL, MAX_ESSAY_SCORE, MIN_ESSAY_SCORE


def parse_decimal(text: str) -> float:
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
    value = text.strip().replace("\xa0", "")
    if not value or value == "-":
        return None
    return int(value.replace(".", "").replace(",", ""))


def parse_optional_decimal(text: str) -> float | None:
    value = text.strip().replace("\xa0", "")
    if not value or value == "-":
        return None
    return parse_decimal(value)


def parse_essay_stats(html: str) -> dict[str, dict[str, float | int | None]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if table is None:
        raise RuntimeError("Tabela de estatísticas da redação não encontrada.")

    stats = {}
    for row in table.find_all("tr"):
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
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return parse_essay_stats(response.text)


def calculate_essay_standard_score(raw_score: float, mean: float, std_dev: float) -> float:
    if not MIN_ESSAY_SCORE <= raw_score <= MAX_ESSAY_SCORE:
        raise ValueError(f"Nota da redação deve estar entre {MIN_ESSAY_SCORE:g} e {MAX_ESSAY_SCORE:g}.")
    if std_dev <= 0:
        raise ValueError("Desvio padrão da redação deve ser maior que zero.")

    return 500 + 100 * ((raw_score - mean) / std_dev)


def compose_port_red_score(portuguese_ep: float, essay_ep: float) -> float:
    return (portuguese_ep + essay_ep) / 2


def compose_port_red_scores(portuguese_scores: list[float], essay_ep: float) -> list[float]:
    return [compose_port_red_score(portuguese_ep, essay_ep) for portuguese_ep in portuguese_scores]


def save_essay_stats_to_json(stats: dict[str, dict], filename: str | Path = "data/redacao_stats.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def save_essay_stats_to_csv(stats: dict[str, dict], filename: str | Path = "data/redacao_stats.csv"):
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
