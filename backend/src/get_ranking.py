import re

from bs4 import BeautifulSoup

from .constants import ENTRY_MODE_PATTERNS, RANKING_URL, STATUS_PATTERNS
from .scripts.save_rankings import create_driver, load_data


def parse_ranking(html: str) -> list[list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "tabDados items modelo1"})

    if table is None:
        raise RuntimeError("Tabela de ranking não encontrada.")

    rows = []
    for row in table.find_all("tr")[1:]:
        cols = [col.get_text(strip=True) for col in row.find_all("td")]
        if cols:
            rows.append(cols)

    return rows


def get_min_AC(ranking: list[list[str]], entry_mode: str) -> float:
    status_regex = re.compile("|".join(STATUS_PATTERNS.values()))
    mode_regex = re.compile(ENTRY_MODE_PATTERNS[entry_mode])

    min_ac = float("inf")
    for candidate in ranking:
        if len(candidate) < 8:
            continue
        if not status_regex.search(candidate[7]):
            continue
        if not mode_regex.search(candidate[6]):
            continue

        try:
            score = float(candidate[3].replace(",", "."))
        except ValueError:
            continue

        min_ac = min(min_ac, score)

    if min_ac == float("inf"):
        raise RuntimeError(f"Nenhuma nota de corte encontrada para {entry_mode}.")

    return min_ac


def get_ranking(year: str, course: str) -> list[list[str]]:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import Select, WebDriverWait

    driver = create_driver()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(RANKING_URL)
        Select(wait.until(EC.presence_of_element_located((By.ID, "selectAno")))).select_by_visible_text(str(year))
        Select(wait.until(EC.element_to_be_clickable((By.ID, "selectConcurso")))).select_by_visible_text("Vestibular")
        Select(wait.until(EC.presence_of_element_located((By.ID, "selectCurso")))).select_by_visible_text(course)
        load_data(driver, wait)
        return parse_ranking(driver.page_source)
    finally:
        driver.quit()
