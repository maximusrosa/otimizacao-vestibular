import json
from pathlib import Path
from ..constants import WEIGHTS_PATH

# Load the mapping into memory once when the server starts
MAPPING_PATH = Path("data/course_mapping.json")
if MAPPING_PATH.exists():
    with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
        _data = json.load(f)
        COURSE_MAPPING = _data.get("mapping", _data)  # backwards-compatible with flat JSON
else:
    COURSE_MAPPING = {}

def readCourseWeights(scraped_course: str):
    # Lookup the normalized base name
    target_base = COURSE_MAPPING.get(scraped_course, scraped_course)
    
    with open(WEIGHTS_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        header = lines[0].strip().split(',')
        subjects = header[1:]
        
        for line in lines[1:]:
            data = line.strip().split(',')
            csv_course = data[0]
            
            if csv_course == target_base:
                weights = data[1:]
                return {subjects[i]: int(weights[i]) for i in range(len(subjects))}
        
        return {}

# Por enquanto notas de corte são constantes, depois fazer um método para tentar obter de cache ou web scraping caso não tenha dados dos anos anteriores para modalidade específica
# Imaginei os dados de Min_AC como um dicionário aninhado, onde a chave é uma tupla (curso, modalidade) e o valor é outro dicionário que mapeia anos para notas de corte. Exemplo:
min_AC = {
    ("Ciência da Computação - Bacharelado", "LI_EP"): 
        {"2025": 750.0, "2024": 740.0, "2023": 730.0, "2022": 720.0, "2021": 710.0, "2020": 700.0,
         "2019": 690.0, "2018": 680.0, "2017": 670.0, "2016": 660.0},
    ("Ciência da Computação - Bacharelado", "LI"): 
        {"2025": 760.0, "2024": 750.0, "2023": 740.0, "2022": 730.0, "2021": 720.0, "2020": 710.0,
        "2019": 700.0, "2018": 690.0, "2017": 680.0, "2016": 670.0}
    }

def getGraphData(reference_year, course, entry_mode):
    key = (course, entry_mode)
    min_acs = {}
    if key in min_AC:
        for year in range(reference_year - 5, reference_year + 1):
            if str(year) in min_AC[key]:
                min_acs[year] = min_AC[key][str(year)]
    
    return min_acs