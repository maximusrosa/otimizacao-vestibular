import requests

from .constants import FOREIGN_LANGUAGES, MAX_HITS, MIN_HITS, SCORES_URL, SUBJECTS
from .scripts.save_scores import _parse_float, parse_all_scores


def parse_scores(html: str, foreign_language: str) -> dict[str, list[float]]:
    if foreign_language not in FOREIGN_LANGUAGES:
        raise ValueError(f"Língua estrangeira inválida: {foreign_language}")

    records = parse_all_scores(html, "0")
    scores = {}
    language_code = f"LEM_{foreign_language.upper()}"

    for record in records:
        discipline = record["disciplina"]
        if discipline.startswith("LEM_"):
            if discipline != language_code:
                continue
            discipline = "LEM"

        scores.setdefault(discipline, {})[record["acertos"]] = record["escore"]

    missing_subjects = set(SUBJECTS) - set(scores)
    if missing_subjects:
        raise RuntimeError(f"Escores incompletos. Disciplinas ausentes: {sorted(missing_subjects)}.")

    parsed_scores = {}
    for subject in SUBJECTS:
        subject_scores = scores[subject]
        expected_hits = set(range(MIN_HITS, MAX_HITS + 1))
        if set(subject_scores) != expected_hits:
            raise RuntimeError(f"{subject} deve ter escores para acertos {MIN_HITS}-{MAX_HITS}.")
        parsed_scores[subject] = [subject_scores[hits] for hits in range(MIN_HITS, MAX_HITS + 1)]

    return parsed_scores


def get_scores(year: str, foreign_language: str) -> dict[str, list[float]]:
    response = requests.get(SCORES_URL.format(year=year), timeout=30)
    response.raise_for_status()
    return parse_scores(response.text, foreign_language)
