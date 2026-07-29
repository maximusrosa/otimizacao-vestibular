import json
import time
from datetime import date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import csv
import difflib
from ..constants import RANKING_URL, WEIGHTS_PATH, MAPPING_PATH


# Manual aliases for historical names that fuzzy matching can't guess logically
ALIASES = {
    "bach. i. em ciência e tecnologia": "Interdisciplinar em Ciência e Tecnologia",
    "ciências jur/soc - direito - diurno": "Ciências Jurídicas e Sociais",
    "ciências jur/soc - direito - noturno": "Ciências Jurídicas e Sociais",
    "com. social - publicidade/propaganda": "Publicidade Propaganda",
    "design - habilitação design produto": "Design de Produto",
    "design - habilitação design visual": "Design Visual",
    "gestão pública e desenvolvimento regional - bacharelado - noturno - camp": "Políticas Públicas"
}

def create_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    return webdriver.Chrome(options=chrome_options)

def scrape_all_course_names():
    print("Iniciando scraping de nomes de cursos...")
    
    driver = create_driver()
    wait = WebDriverWait(driver, 15)
    
    unique_courses = set()

    try:
        print(f"Acessando {RANKING_URL}...")
        driver.get(RANKING_URL)

        # 1. Pega todos os anos disponíveis
        dropdown_ano = wait.until(EC.presence_of_element_located((By.ID, "selectAno")))
        select_ano = Select(dropdown_ano)
        # Filtra opções vazias ou "Selecione..."
        years = [opt.text.strip() for opt in select_ano.options if "Selecione" not in opt.text and opt.text.strip() != ""]

        print(f"Anos encontrados: {years}")

        for year in years:
            print(f"Extraindo cursos para o ano de {year}...")
            
            try:
                dropdown_ano = wait.until(EC.presence_of_element_located((By.ID, "selectAno")))
                Select(dropdown_ano).select_by_visible_text(year)
                # Dá um pequeno tempo para o AJAX iniciar a transição
                time.sleep(1) 
            except Exception as e:
                print(f"  [Erro] Falha ao selecionar ano {year}: {e}")
                continue

            try:
                # Espera o selectConcurso ser repopulado
                wait.until(lambda d: len(Select(d.find_element(By.ID, "selectConcurso")).options) > 1)
                
                # Busca fresca no DOM
                dropdown_concurso = driver.find_element(By.ID, "selectConcurso") 
                select_concurso = Select(dropdown_concurso)
                
                vestibular_option = None
                for opt in select_concurso.options:
                    if "Vestibular" in opt.text:
                        vestibular_option = opt.text
                        break
                
                if vestibular_option:
                    select_concurso.select_by_visible_text(vestibular_option)
                else:
                    select_concurso.select_by_index(1)
                
                # Dá um tempo para o AJAX de cursos iniciar
                time.sleep(1) 

            except Exception as e:
                print(f"  [Aviso] Não foi possível selecionar o concurso em {year}: {e}")
                continue

            try:
                # O segredo contra o StaleElement: esperar as opções carregarem e DEPOIS referenciar o elemento novamente
                wait.until(lambda d: len(Select(d.find_element(By.ID, "selectCurso")).options) > 1)
                
                dropdown_curso = driver.find_element(By.ID, "selectCurso") # Referência nova!
                select_curso = Select(dropdown_curso)
                
                for opt in select_curso.options:
                    course_name = opt.text.strip()
                    if course_name and "Selecione" not in course_name:
                        unique_courses.add(course_name)
                        
            except Exception as e:
                print(f"  [Aviso] Não foi possível carregar os cursos em {year}: {e}")

    finally:
        driver.quit()

    print(f"Concluído! Foram encontradas {len(unique_courses)} variações únicas.")

    return sorted(list(unique_courses))


def generate_mapping(variations:list[str]):
    print(f"Gerando mapeamento para {len(variations)} variações de cursos...")
    
    # 1. Load targets from the weights CSV
    targets = []
    with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row:
                targets.append(row[0].strip())

    # 2. Match variations to targets
    mapping = {}

    for var in variations:
        search_var = var.lower()
        
        # Apply aliases first
        if search_var in ALIASES:
            search_var = ALIASES[search_var].lower()
            
        possible_substring_matches = []
        
        # Check simple base matching (e.g. "Agronomia - Noturno" contains "Agronomia")
        for target in targets:
            target_base = target.split(' - ')[0]
            if target_base.lower() in search_var:
                possible_substring_matches.append(target)
                
        # Substring resolution
        if len(possible_substring_matches) == 1:
            mapping[var] = possible_substring_matches[0]
            continue
        elif len(possible_substring_matches) > 1:
            # Use fuzzy matching as a tiebreaker
            matches = difflib.get_close_matches(search_var, [t.lower() for t in possible_substring_matches], n=1, cutoff=0.3)
            if matches:
                idx = [t.lower() for t in possible_substring_matches].index(matches[0])
                mapping[var] = possible_substring_matches[idx]
                continue
                
        # Fuzzy match fallback
        matches = difflib.get_close_matches(search_var, [t.lower() for t in targets], n=1, cutoff=0.6)
        if matches:
            idx = [t.lower() for t in targets].index(matches[0])
            mapping[var] = targets[idx]
        else:
            mapping[var] = "NEEDS_REVIEW"

    # 3. Save the mapping
    sorted_mapping = {k: mapping[k] for k in sorted(mapping.keys())}
    output = {"last_updated": date.today().isoformat(), "mapping": sorted_mapping}

    with open(MAPPING_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
        
    needs_review = [k for k, v in mapping.items() if v == "NEEDS_REVIEW"]
    
    print(f"Mapeamento gerado com sucesso e salvo em {MAPPING_PATH}.")
    
    if needs_review:
        print("\nPrecisam de revisão manual:")
        for item in needs_review:
            print(f" - {item}")

if __name__ == '__main__':
    variations = scrape_all_course_names()
    generate_mapping(variations)