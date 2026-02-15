from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from constants import MODE_PATTERNS, INF
import re

URL = "https://www1.ufrgs.br/PortalEnsino/GraduacaoProcessoSeletivo/index.php/DivulgacaoDadosChamamento"


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

    print(f"Foram encontrados {len(select_course.options) - 1} cursos disponíveis.")
    select_course.select_by_visible_text(course)


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
def getRanking(year: str, exam: str, course: str) -> list[list[str]]:
    driver = create_driver()
    wait = WebDriverWait(driver, 10)
    
    try:
        driver.get(URL)

        select_year(driver, wait, year)
        select_exam(driver, wait, exam)
        select_course(driver, wait, course)
        load_data(driver, wait)

        soup = BeautifulSoup(driver.page_source, "html.parser")

    finally:
        driver.quit()
        
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


def getMinAC(ranking: list[list[str]], target_mode: str) -> float:
    pattern_str = MODE_PATTERNS.get(target_mode)
    pattern = re.compile(pattern_str) # type: ignore (vamos filtrar no front para estar em ENTRY_MODES)
    
    min_score = INF

    for candidate in ranking:
        score = float(candidate[3])  # Média
        entry_mode = candidate[6]  # Vaga de ingresso
        status = candidate[7]  # Situação

        if pattern.search(entry_mode) and status in ["Matriculado", "Lotado em vaga"]:                    
                if score < min_score:
                    min_score = score

    if min_score != INF:
        return min_score
    else:
        raise RuntimeError(f"Nenhuma nota encontrada para a modalidade: {target_mode}")


def main():
    year = "2026"
    exam = "Vestibular"
    course = "Ciência da Computação - Bacharelado"
    target_mode = "LI_EP"

    ranking = getRanking(year, exam, course)
    min_score = getMinAC(ranking, target_mode)

    print(f"A nota de corte para {target_mode} é: {min_score}")

if __name__ == "__main__":
    main()