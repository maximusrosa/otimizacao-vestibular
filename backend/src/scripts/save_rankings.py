import json
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

from ..constants import RANKING_URL
from .utils import COURSE_MAPPING

# SALVAMENTO EM ARQUIVOS (JSON e CSV)

def save_rankings_to_json(todos_registros, filename="data/rankings_completos.json"):
    """Salva a lista de dicionários em um arquivo JSON."""
    with open(filename, mode='w', encoding='utf-8') as f:
        json.dump(todos_registros, f, ensure_ascii=False, indent=2)

def save_rankings_to_csv(todos_registros, filename="data/rankings_completos.csv"):
    """Salva a lista de dicionários em um arquivo CSV."""
    if not todos_registros:
        return
        
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        # Pega as chaves do primeiro dicionário para fazer o cabeçalho
        colunas = list(todos_registros[0].keys())
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(todos_registros)

# SELENIUM & SCRAPING

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    return webdriver.Chrome(options=chrome_options)

def load_data(driver, wait):
    button_load = wait.until(EC.element_to_be_clickable((By.ID, "btnCarregarDados")))
    button_load.click()
    # Espera a tabela de resultados aparecer
    xpath_dados = "/html/body/div[1]/fieldset[3]/div[2]/div/div/table//tr[2]"
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath_dados)))

def parse_ranking_for_json(html: str, year: int, canonical_course: str) -> list[dict]:
    """
    Lê o HTML da tabela e extrai apenas os dados relevantes.
    Retorna uma lista de DICIONÁRIOS, perfeitos para virarem JSON.
    """
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", {"class": "tabDados items modelo1"})

    if table is None:
        return []

    rows = table.find_all("tr")[1:] # Pula o cabeçalho
    registros = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 8:
            continue
            
        try:
            score = float(cols[3].text.strip().replace(',', '.'))
        except ValueError:
            score = 0.0
            
        entry_mode = cols[6].text.strip()
        status = cols[7].text.strip()
        
        # Cria um dicionário ao invés de tupla
        registros.append({
            "ano": year,
            "curso": canonical_course,
            "nota_final": score,
            "modalidade": entry_mode,
            "situacao": status
        })

    return registros


def fetch_rankings_for_year(year: str, driver=None) -> list[dict]:
    owns_driver = driver is None
    if owns_driver:
        driver = create_driver()

    wait = WebDriverWait(driver, 10)
    registros_do_ano = []

    try:
        driver.get(RANKING_URL)

        select_year_obj = Select(wait.until(EC.presence_of_element_located((By.ID, "selectAno"))))
        select_year_obj.select_by_visible_text(str(year))

        time.sleep(1.5)

        dropdown_exam = wait.until(EC.element_to_be_clickable((By.ID, "selectConcurso")))
        select_exam_obj = Select(dropdown_exam)

        try:
            select_exam_obj.select_by_visible_text("Vestibular")
        except NoSuchElementException:
            print(f"  [AVISO] Concurso 'Vestibular' não encontrado em {year}.")
            return []

        time.sleep(2)

        dropdown_course = wait.until(EC.presence_of_element_located((By.ID, "selectCurso")))
        select_course_obj = Select(dropdown_course)

        opcoes_cursos = []
        for opt in select_course_obj.options:
            text = opt.text.strip()
            if text and "Selecione" not in text:
                opcoes_cursos.append(text)

        for course_text in opcoes_cursos:
            canonical_course = COURSE_MAPPING.get(course_text, course_text)
            print(f"  -> Raspando: {canonical_course} (Nome no site: {course_text})")

            try:
                dropdown_course = wait.until(EC.presence_of_element_located((By.ID, "selectCurso")))
                Select(dropdown_course).select_by_visible_text(course_text)

                load_data(driver, wait)

                registros = parse_ranking_for_json(driver.page_source, int(year), canonical_course)
                registros_do_ano.extend(registros)

            except Exception as e:
                print(f"     [ERRO] Falha ao processar {course_text}: {e}")

        return registros_do_ano
    finally:
        if owns_driver:
            driver.quit()



def main():
    anos_alvo = [str(i) for i in range(2016, 2026)]
    
    todos_os_registros = [] # Acumulador para o JSON/CSV
    
    driver = create_driver()
    wait = WebDriverWait(driver, 10)

    try:
        driver.get(RANKING_URL)

        for year in anos_alvo:
            print(f"\n=== Iniciando extração do ano {year} ===")
            todos_os_registros.extend(fetch_rankings_for_year(year, driver=driver))

    finally:
        driver.quit()

    print("\nGerando arquivos com todos os dados consolidados...")
    save_rankings_to_json(todos_os_registros, "data/rankings_completos.json")
    save_rankings_to_csv(todos_os_registros, "data/rankings_completos.csv")
    print("Processo 100% concluído! Arquivo salvo em 'data/rankings_completos.json'")

if __name__ == "__main__":
    main()
