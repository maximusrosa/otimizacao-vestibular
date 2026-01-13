from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

url = "https://www1.ufrgs.br/PortalEnsino/GraduacaoProcessoSeletivo/index.php/DivulgacaoDadosChamamento"

year = "2025"

exam = "Vestibular"

course = "Ciência da Computação - Bacharelado"

entry_method = "L3/L5/LI_EP"

# Configuração do Driver
driver = webdriver.Chrome()

try:
    driver.get(url)
    wait = WebDriverWait(driver, 10)

    # ----- Seleção --------
    # Seleciona o Ano
    select_year = Select(wait.until(EC.presence_of_element_located((By.ID, "selectAno"))))
    select_year.select_by_visible_text(year)

    # Seleciona o Concurso
    dropdown_exam = wait.until(EC.element_to_be_clickable((By.ID, "selectConcurso")))
    select_exam = Select(dropdown_exam)
    wait.until(lambda d: len(select_exam.options) > 1)
    select_exam.select_by_visible_text(exam)

    # ----- Extrai opções de Curso  --------
    # Extrai opções do botão de Curso
    dropdown_course = wait.until(EC.presence_of_element_located((By.ID, "selectCurso")))
    select_course = Select(dropdown_course)
    
    # Aguarda as opções carregarem (ignorando a opção default "-- Selecione --")
    wait.until(lambda d: len(select_course.options) > 1)

    print(f"Foram encontrados {len(select_course.options) - 1} cursos disponíveis:")
    
    # ----- Seleciona o curso ------
    select_course.select_by_visible_text(course)

    # Clica no botão "Carregar Dados"
    button_load = wait.until(EC.element_to_be_clickable((By.ID, "btnCarregarDados")))
    button_load.click()

    # Aguarda a tabela de dados carregar
    xpath_dados = "/html/body/div[1]/fieldset[3]/div[2]/div/div/table//tr[2]"
    WebDriverWait(driver, 15).until(
        EC.presence_of_element_located((By.XPATH, xpath_dados))
    )
    
    # ----- Extrai dados da tabela (com Beautiful Soup) ------
    page_html = driver.page_source
    soup = BeautifulSoup(page_html, 'html.parser')

    table = soup.find('table', {'class': 'tabDados items modelo1'})
    
    if table is None:
        print("Tabela de dados não encontrada.")
        exit()
    else:
        rows = table.find_all('tr')[1:]
        print(f"\nDados extraídos para o curso selecionado:")
        for row in rows:
            columns = row.find_all('td')
            if columns:
                data = [col.text.strip() for col in columns]
                print(data)

finally:
    driver.quit()