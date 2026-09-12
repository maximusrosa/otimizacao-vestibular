import argparse
import csv
import json
import os
import shutil
from datetime import datetime
from pathlib import Path

import requests

from ..constants import (
    FOREIGN_LANGUAGES,
    MAX_HITS,
    MIN_HITS,
    SCORES_URL,
    SUBJECT_NAME_TO_CODE,
)
from ..essay_scores import fetch_essay_stats
from .save_rankings import fetch_rankings_for_year
from .save_scores import parse_all_scores


DATA_DIR = Path("data")
SCORES_JSON = DATA_DIR / "escores_padronizados.json"
SCORES_CSV = DATA_DIR / "escores_padronizados.csv"
RANKINGS_JSON = DATA_DIR / "rankings_completos.json"
RANKINGS_CSV = DATA_DIR / "rankings_completos.csv"
ESSAY_JSON = DATA_DIR / "redacao_stats.json"
ESSAY_CSV = DATA_DIR / "redacao_stats.csv"


def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def atomic_write_json(path: Path, data):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp_path, path)


def atomic_write_csv(path: Path, fieldnames: list[str], rows: list[dict]):
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp_path, path)


def backup_existing_files(paths: list[Path]) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = DATA_DIR / "backups" / timestamp
    backup_dir.mkdir(parents=True, exist_ok=True)

    for path in paths:
        if path.exists():
            shutil.copy2(path, backup_dir / path.name)

    return backup_dir


def records_to_nested_scores(records: list[dict]) -> dict[str, dict[str, float]]:
    nested = {}
    for record in records:
        discipline = record["disciplina"]
        hits = str(record["acertos"])
        nested.setdefault(discipline, {})[hits] = record["escore"]
    return nested


def nested_scores_to_csv_rows(scores_data: dict) -> list[dict]:
    rows = []
    for year in sorted(scores_data, key=int):
        for discipline in sorted(scores_data[year]):
            scores = scores_data[year][discipline]
            for hits in sorted(scores, key=int):
                rows.append(
                    {
                        "ano": int(year),
                        "disciplina": discipline,
                        "acertos": int(hits),
                        "escore": scores[hits],
                    }
                )
    return rows


def rankings_to_csv_rows(rankings_data: list[dict]) -> list[dict]:
    return sorted(rankings_data, key=lambda row: (int(row["ano"]), row["curso"], row["modalidade"], -row["nota_final"]))


def essay_to_csv_rows(essay_data: dict) -> list[dict]:
    rows = []
    for year in sorted(essay_data, key=int):
        rows.append({"year": year, **essay_data[year]})
    return rows


def fetch_scores_for_year(year: str) -> dict[str, dict[str, float]]:
    response = requests.get(SCORES_URL.format(year=year), timeout=30)
    response.raise_for_status()

    records = parse_all_scores(response.text, year)
    nested = records_to_nested_scores(records)
    validate_scores_for_year(year, nested)
    return nested


def validate_scores_for_year(year: str, scores: dict[str, dict[str, float]]):
    expected_disciplines = set(SUBJECT_NAME_TO_CODE.values()) | {f"LEM_{language.upper()}" for language in FOREIGN_LANGUAGES}
    missing = expected_disciplines - set(scores)
    if missing:
        raise RuntimeError(f"Escores de {year} incompletos. Disciplinas ausentes: {sorted(missing)}.")

    expected_hits = {str(hit) for hit in range(MIN_HITS, MAX_HITS + 1)}
    for discipline, discipline_scores in scores.items():
        hits = set(discipline_scores)
        if hits != expected_hits:
            raise RuntimeError(
                f"{discipline} em {year} deve ter acertos {MIN_HITS}-{MAX_HITS}. Ausentes: {sorted(expected_hits - hits)}."
            )
        if any(score <= 0 for score in discipline_scores.values()):
            raise RuntimeError(f"{discipline} em {year} possui escore padronizado menor ou igual a zero.")


def validate_rankings_for_year(year: str, rankings: list[dict]):
    if not rankings:
        raise RuntimeError(f"Nenhum ranking foi encontrado para {year}.")
    if any(str(row["ano"]) != year for row in rankings):
        raise RuntimeError(f"Rankings retornaram registros fora do ano {year}.")


def validate_essay_for_year(year: str, essay_data: dict):
    if year not in essay_data:
        raise RuntimeError(f"Estatísticas de redação de {year} não encontradas.")
    stats = essay_data[year]
    if stats["std_dev"] <= 0:
        raise RuntimeError(f"Desvio padrão inválido para redação de {year}.")


def update_year_data(year: str, dry_run: bool = False, force: bool = False):
    scores_data = load_json(SCORES_JSON, {})
    rankings_data = load_json(RANKINGS_JSON, [])
    essay_data = load_json(ESSAY_JSON, {})

    ranking_year_exists = any(str(row["ano"]) == year for row in rankings_data)
    if not force and (year in scores_data or ranking_year_exists or year in essay_data):
        raise RuntimeError(f"O ano {year} já existe na base. Use --force para substituir.")

    print(f"Baixando escores objetivos de {year}...")
    scores_for_year = fetch_scores_for_year(year)

    print("Baixando estatísticas de redação...")
    fetched_essay_data = fetch_essay_stats()
    validate_essay_for_year(year, fetched_essay_data)

    print(f"Baixando rankings de {year}...")
    rankings_for_year = fetch_rankings_for_year(year)
    validate_rankings_for_year(year, rankings_for_year)

    updated_scores = {**scores_data, year: scores_for_year}
    updated_rankings = [row for row in rankings_data if str(row["ano"]) != year] + rankings_for_year
    updated_essay = {**essay_data, **fetched_essay_data}

    validate_scores_for_year(year, updated_scores[year])
    validate_rankings_for_year(year, [row for row in updated_rankings if str(row["ano"]) == year])
    validate_essay_for_year(year, updated_essay)

    if dry_run:
        print("Dry-run concluído: dados válidos, nenhum arquivo foi alterado.")
        return

    backup_dir = backup_existing_files([SCORES_JSON, SCORES_CSV, RANKINGS_JSON, RANKINGS_CSV, ESSAY_JSON, ESSAY_CSV])
    print(f"Backup criado em {backup_dir}")

    atomic_write_json(SCORES_JSON, updated_scores)
    atomic_write_csv(
        SCORES_CSV,
        ["ano", "disciplina", "acertos", "escore"],
        nested_scores_to_csv_rows(updated_scores),
    )

    atomic_write_json(RANKINGS_JSON, updated_rankings)
    atomic_write_csv(
        RANKINGS_CSV,
        ["ano", "curso", "nota_final", "modalidade", "situacao"],
        rankings_to_csv_rows(updated_rankings),
    )

    atomic_write_json(ESSAY_JSON, updated_essay)
    atomic_write_csv(
        ESSAY_CSV,
        ["year", "mean", "std_dev", "corrected_count", "corrected_percentage"],
        essay_to_csv_rows(updated_essay),
    )

    print(f"Base atualizada com sucesso para {year}.")


def main():
    parser = argparse.ArgumentParser(description="Atualiza a base anual do Vestibular UFRGS com validação e backup.")
    parser.add_argument("--year", required=True, help="Ano do vestibular a atualizar, por exemplo 2026.")
    parser.add_argument("--dry-run", action="store_true", help="Valida a atualização sem alterar arquivos.")
    parser.add_argument("--force", action="store_true", help="Substitui dados existentes do ano informado.")
    args = parser.parse_args()

    update_year_data(args.year, dry_run=args.dry_run, force=args.force)


if __name__ == "__main__":
    main()
