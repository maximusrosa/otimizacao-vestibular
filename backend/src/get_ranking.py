from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from .constants import ENTRY_MODE_PATTERNS, STATUS_PATTERNS, INF, RANKING_URL
from .scripts.utils import COURSE_MAPPING
import re


def create_driver():
    """Cria e configura o driver do Selenium em modo headless"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Roda sem interface gráfica
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    return webdriver.Chrome(options=chrome_options)


# ---------- Seleções ----------
def select_year(driver, wait, year: str):
    select_year = Select(wait.until(
        EC.presence_of_element_located((By.ID, "selectAno"))
    ))
    select_year.select_by_visible_text(year)


def select_exam(driver, wait, exam: str):
    dropdown_exam = wait.until(
        EC.element_to_be_clickable((By.ID, "selectConcurso"))
    )
    select_exam = Select(dropdown_exam)
    wait.until(lambda d: len(select_exam.options) > 1)
    select_exam.select_by_visible_text(exam)


def select_course(driver, wait, course: str):
    dropdown_course = wait.until(
        EC.presence_of_element_located((By.ID, "selectCurso"))
    )
    select_course = Select(dropdown_course)
    wait.until(lambda d: len(select_course.options) > 1)

    # O nome do curso no dropdown varia por ano (ex.: "Ciência da Computação"
    # em 2022 vs. "Ciência da Computação - Bacharelado" em 2025). O front envia
    # sempre o nome canônico, então resolvemos cada opção pelo COURSE_MAPPING e
    # escolhemos aquela cujo nome canônico bate com o solicitado.
    for option in select_course.options:
        text = option.text.strip()
        if COURSE_MAPPING.get(text, text) == course:
            select_course.select_by_visible_text(text)
            return

    raise RuntimeError(f"Curso não encontrado no dropdown: {course}")


# ---------- Carregar Dados ----------
def load_data(driver, wait):
    button_load = wait.until(
        EC.element_to_be_clickable((By.ID, "btnCarregarDados"))
    )
    button_load.click()

    xpath_dados = "/html/body/div[1]/fieldset[3]/div[2]/div/div/table//tr[2]"
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, xpath_dados))
    )


# ---------- Extração ----------
def parse_ranking(html: str) -> list[list[str]]:
    """Extrai a tabela de ranking a partir do HTML da página de chamamento."""
    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", {"class": "tabDados items modelo1"})

    if table is None:
        raise RuntimeError("Tabela de dados não encontrada.")

    rows = table.find_all("tr")[1:]
    ranking = []

    for row in rows:
        columns = row.find_all("td")
        candidate = [col.text.strip() for col in columns]
        ranking.append(candidate)

    return ranking


def get_ranking(year: str, course: str, exam:str="Vestibular") -> list[list[str]]:
    driver = create_driver()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(RANKING_URL)

        select_year(driver, wait, year)
        select_exam(driver, wait, exam)
        select_course(driver, wait, course)
        load_data(driver, wait)

        html = driver.page_source

    finally:
        driver.quit()

    return parse_ranking(html)


def get_min_AC(ranking: list[list[str]], target_mode: str) -> float:
    pattern_str = ENTRY_MODE_PATTERNS.get(target_mode)
    pattern = re.compile(pattern_str) # type: ignore (vamos filtrar no front para estar em ENTRY_MODES)

    status_pattern = re.compile("|".join(STATUS_PATTERNS.values()))

    min_score = INF

    for candidate in ranking:
        score = float(candidate[3])  # Média
        entry_mode = candidate[6]  # Vaga de ingresso
        status = candidate[7]  # Situação

        if pattern.search(entry_mode) and status_pattern.search(status):
                if score < min_score:
                    min_score = score

    if min_score != INF:
        return min_score
    else:
        raise RuntimeError(f"Nenhuma nota encontrada para a modalidade: {target_mode}")


def main():
    year = "2022"
    course = "Ciência da Computação"
    target_mode = "LI_EP"

    ranking = get_ranking(year, course)
    min_score = get_min_AC(ranking, target_mode)

    print(f"A nota de corte para {target_mode} é: {min_score}")

if __name__ == "__main__":
    main()