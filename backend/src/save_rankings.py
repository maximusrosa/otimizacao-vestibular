"""Coleta e parsing das tabelas públicas de candidatos da UFRGS."""

import csv
import json
import re
import time
import unicodedata
from datetime import datetime

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .constants import RANKING_URL
from .ranking_repository import candidate_key, normalize_entry_mode
from .utils import COURSE_MAPPING


HEADER_ALIASES = {
    "source_classification": {"classif", "classificacao", "classificacao geral"},
    "registration": {"inscricao", "numero de inscricao"},
    "name": {"nome", "nome do candidato"},
    "final_score": {"media", "media final", "nota final"},
    "remapped_vacancy": {"vaga remanejada", "vaga de remanejamento"},
    "competition_vacancies": {"vaga s de concorrencia", "vagas de concorrencia", "vaga de concorrencia"},
    "entry_vacancy": {"vaga de ingresso"},
    "status": {"situacao"},
    "status_date": {"data da situacao", "data situacao"},
}
REQUIRED_HEADERS = {
    "source_classification",
    "registration",
    "name",
    "final_score",
    "remapped_vacancy",
    "competition_vacancies",
    "entry_vacancy",
    "status",
    "status_date",
}


def normalize_header(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    normalized = re.sub(r"[^a-zA-Z0-9]+", " ", normalized).strip().lower()
    return normalized


def _header_key(value: str) -> str | None:
    normalized = normalize_header(value)
    for key, aliases in HEADER_ALIASES.items():
        if normalized in aliases:
            return key
    return None


def _parse_score(value: str) -> float:
    value = value.strip()
    if "," in value:
        value = value.replace(".", "").replace(",", ".")
    return float(value)


def _parse_status_date(value: str) -> str | None:
    value = value.strip()
    if not value or value in {"-", "—"}:
        return None
    for date_format in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"Data de situação inválida: {value}.")


def parse_candidate_table(html: str, year: int, canonical_course: str, source_course: str | None = None) -> list[dict]:
    """Extrai candidatos identificando as colunas pelo cabeçalho publicado."""
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "tabDados items modelo1"})
    if table is None:
        raise RuntimeError("Tabela de ranking não encontrada.")

    header_cells = table.find("tr").find_all(["th", "td"])
    indexes = {}
    for index, cell in enumerate(header_cells):
        key = _header_key(cell.get_text(" ", strip=True))
        if key and key not in indexes:
            indexes[key] = index

    missing_headers = REQUIRED_HEADERS - set(indexes)
    if missing_headers:
        raise RuntimeError(f"Colunas obrigatórias ausentes no ranking: {sorted(missing_headers)}.")

    candidates = []
    source_course = source_course or canonical_course
    for row in table.find_all("tr")[1:]:
        cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
        if not cells:
            continue

        def value(key: str) -> str:
            index = indexes.get(key)
            return cells[index].strip() if index is not None and index < len(cells) else ""

        registration = value("registration")
        name = value("name")
        if not registration or not name:
            continue

        entry_vacancy = value("entry_vacancy")
        competition = value("competition_vacancies")
        mode_source = entry_vacancy or competition
        candidates.append(
            {
                "candidate_key": candidate_key(year, canonical_course, registration),
                "source_course": source_course,
                "source_classification": value("source_classification") or None,
                "name": name,
                "final_score": _parse_score(value("final_score")),
                "remapped_vacancy": value("remapped_vacancy") or None,
                "competition_vacancies": competition or None,
                "entry_vacancy": entry_vacancy,
                "entry_mode": normalize_entry_mode(mode_source),
                "status": value("status"),
                "status_date": _parse_status_date(value("status_date")),
            }
        )
    return candidates


def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1440,1200")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(45)
    return driver


def load_data(driver, wait):
    button = wait.until(EC.element_to_be_clickable((By.ID, "btnCarregarDados")))
    button.click()
    WebDriverWait(driver, 45).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "table.tabDados.items.modelo1 tr:nth-child(2)"))
    )


def select_year_and_exam(driver, wait, year: int | str) -> list[str]:
    driver.get(RANKING_URL)
    Select(wait.until(EC.presence_of_element_located((By.ID, "selectAno")))).select_by_visible_text(str(year))
    time.sleep(1.5)

    exam = Select(wait.until(EC.element_to_be_clickable((By.ID, "selectConcurso"))))
    wait.until(lambda _driver: len(exam.options) > 1)
    try:
        exam.select_by_visible_text("Vestibular")
    except NoSuchElementException as error:
        raise RuntimeError(f"Concurso Vestibular não encontrado para {year}.") from error
    time.sleep(2)

    courses = Select(wait.until(EC.presence_of_element_located((By.ID, "selectCurso"))))
    wait.until(lambda _driver: len(courses.options) > 1)
    return [
        option.text.strip()
        for option in courses.options
        if option.text.strip() and "Selecione" not in option.text
    ]


def fetch_course_candidates(
    driver,
    year: int,
    source_course: str,
    *,
    retries: int = 3,
) -> tuple[str, list[dict]]:
    canonical_course = COURSE_MAPPING.get(source_course, source_course)
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            wait = WebDriverWait(driver, 15)
            dropdown = Select(wait.until(EC.presence_of_element_located((By.ID, "selectCurso"))))
            dropdown.select_by_visible_text(source_course)
            load_data(driver, wait)
            candidates = parse_candidate_table(driver.page_source, year, canonical_course, source_course)
            if not candidates:
                raise RuntimeError("Tabela carregada sem candidatos.")
            return canonical_course, candidates
        except Exception as error:
            last_error = error
            if attempt < retries:
                time.sleep(2 ** (attempt - 1))
                select_year_and_exam(driver, WebDriverWait(driver, 15), year)
    raise RuntimeError(f"Falha ao coletar {source_course} após {retries} tentativas: {last_error}") from last_error


def fetch_rankings_for_year(year: str, driver=None) -> list[dict]:
    """Compatibilidade: coleta todos os candidatos detalhados de um ano."""
    owns_driver = driver is None
    driver = driver or create_driver()
    candidates = []
    try:
        courses = select_year_and_exam(driver, WebDriverWait(driver, 15), year)
        for source_course in courses:
            _course, course_candidates = fetch_course_candidates(driver, int(year), source_course)
            candidates.extend(course_candidates)
            time.sleep(1.5)
        return candidates
    finally:
        if owns_driver:
            driver.quit()


def parse_ranking_for_json(html: str, year: int, canonical_course: str) -> list[dict]:
    """Formato legado mantido apenas para consumidores antigos."""
    return [
        {
            "ano": year,
            "curso": canonical_course,
            "nota_final": candidate["final_score"],
            "modalidade": candidate["entry_vacancy"],
            "situacao": candidate["status"],
        }
        for candidate in parse_candidate_table(html, year, canonical_course)
    ]


def save_rankings_to_json(records, filename="data/rankings_completos.json"):
    with open(filename, "w", encoding="utf-8") as destination:
        json.dump(records, destination, ensure_ascii=False, indent=2)


def save_rankings_to_csv(records, filename="data/rankings_completos.csv"):
    if not records:
        return
    with open(filename, "w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
