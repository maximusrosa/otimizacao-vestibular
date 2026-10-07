import re

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

from .constants import ENTRY_MODE_PATTERNS, RANKING_URL, STATUS_PATTERNS
from .save_rankings import create_driver, load_data


def select_year(driver, wait, year: str):
    Select(wait.until(EC.presence_of_element_located((By.ID, "selectAno")))).select_by_visible_text(str(year))


def select_exam(driver, wait, exam: str):
    dropdown = wait.until(EC.element_to_be_clickable((By.ID, "selectConcurso")))
    selector = Select(dropdown)
    wait.until(lambda _driver: len(selector.options) > 1)
    selector.select_by_visible_text(exam)


def get_available_courses(year: str, exam: str = "Vestibular") -> list[str]:
    """Consulta cursos diretamente no site; a API normal usa a base anual local."""
    driver = create_driver()
    wait = WebDriverWait(driver, 10)
    try:
        driver.get(RANKING_URL)
        select_year(driver, wait, year)
        select_exam(driver, wait, exam)
        dropdown = wait.until(EC.presence_of_element_located((By.ID, "selectCurso")))
        selector = Select(dropdown)
        wait.until(lambda _driver: len(selector.options) > 1)
        return [option.text.strip() for option in selector.options[1:]]
    finally:
        driver.quit()


def parse_ranking(html: str) -> list[list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "tabDados items modelo1"})
    if table is None:
        raise RuntimeError("Tabela de ranking não encontrada.")

    return [
        [column.get_text(strip=True) for column in row.find_all("td")]
        for row in table.find_all("tr")[1:]
        if row.find_all("td")
    ]


def get_min_AC(ranking: list[list[str]], entry_mode: str) -> float:
    if entry_mode not in ENTRY_MODE_PATTERNS:
        raise ValueError(f"Modalidade de ingresso inválida: {entry_mode}.")

    status_regex = re.compile("|".join(STATUS_PATTERNS.values()))
    mode_regex = re.compile(ENTRY_MODE_PATTERNS[entry_mode])
    scores = []

    for candidate in ranking:
        if len(candidate) < 8 or not status_regex.search(candidate[7]) or not mode_regex.search(candidate[6]):
            continue
        try:
            scores.append(float(candidate[3].replace(",", ".")))
        except ValueError:
            continue

    if not scores:
        raise RuntimeError(f"Nenhuma nota de corte encontrada para {entry_mode}.")
    return min(scores)


def get_ranking(year: str, course: str) -> list[list[str]]:
    driver = create_driver()
    wait = WebDriverWait(driver, 10)
    try:
        driver.get(RANKING_URL)
        select_year(driver, wait, year)
        select_exam(driver, wait, "Vestibular")
        course_select = Select(wait.until(EC.presence_of_element_located((By.ID, "selectCurso"))))
        wait.until(lambda _driver: len(course_select.options) > 1)
        course_select.select_by_visible_text(course)
        load_data(driver, wait)
        return parse_ranking(driver.page_source)
    finally:
        driver.quit()
