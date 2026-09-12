import json
import requests
import csv
from bs4 import BeautifulSoup
from ..constants import (
    MIN_HITS, MAX_HITS, SCORES_URL, SUBJECT_NAME_TO_CODE, FOREIGN_LANGUAGES
)

def _parse_float(text: str) -> float:
    text = text.strip()
    last_sep = max(text.rfind("."), text.rfind(","))
    if last_sep == -1:
        return float(text)
    integer = text[:last_sep].replace(".", "").replace(",", "")
    frac = text[last_sep + 1:]
    return float(f"{integer}.{frac}")

def _parse_std_scores(table) -> dict[int, float]:
    tbody = table.find("tbody")
    if not tbody:
        return {}

    scores = {}
    for tr in tbody.find_all("tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) < 2:
            continue
        hits = int(cols[0])
        scores[hits] = _parse_float(cols[1])
    return scores


def parse_all_scores(html: str, year: str) -> list[dict]:
    """Retorna uma lista de dicionários com os dados de cada acerto"""
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("div", class_="row")

    registros = []
    disciplinas_processadas = set()

    for row in rows:
        cols = row.select("div.col.s12.m6")
        if len(cols) < 2:
            continue

        table_heading = cols[1].select_one("table.col.s12")
        if not table_heading:
            continue

        th = table_heading.select_one("thead tr th[colspan='2']")
        if not th:
            continue

        subject = th.get_text(strip=True)

        if subject in SUBJECT_NAME_TO_CODE:
            code = SUBJECT_NAME_TO_CODE[subject]
        elif subject in FOREIGN_LANGUAGES:
            code = f"LEM_{subject.upper()}"
        else:
            continue

        if code in disciplinas_processadas:
            continue
            
        disciplinas_processadas.add(code)

        table = cols[0].select_one("table.col.s12")
        if not table:
            continue

        scores = _parse_std_scores(table)

        for hits in range(MIN_HITS, MAX_HITS + 1):
            if hits in scores:
                escore_padronizado = scores[hits]
                # Criando um dicionário ao invés de tupla
                registros.append({
                    "ano": int(year),
                    "disciplina": code,
                    "acertos": hits,
                    "escore": escore_padronizado
                })

    return registros


# CSV e JSON

def save_scores_to_csv(todos_registros, filename="data/escores_padronizados.csv"):
    if not todos_registros:
        return
    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        colunas = ["ano", "disciplina", "acertos", "escore"]
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(todos_registros)


def save_scores_to_json(dados_aninhados, filename="data/escores_padronizados.json"):
    """Salva a estrutura de dicionários aninhados em JSON"""
    with open(filename, mode='w', encoding='utf-8') as f:
        json.dump(dados_aninhados, f, ensure_ascii=False, indent=2)


def main():
    anos_para_baixar = [str(i) for i in range(2008, 2027)]
    
    flat_csv_data = [] # Lista plana (tabela) para o CSV
    nested_json_data = {} # Dicionário otimizado para a API (O(1))
    
    for year in anos_para_baixar:
        print(f"Baixando e processando escores do ano {year}...")
        
        url = SCORES_URL.format(year=year)
        response = requests.get(url)
        
        # Prevenção caso a url do ano não exista
        if response.status_code != 200:
            print(f"  -> Página não encontrada para {year}. Pulando...")
            continue
            
        registros = parse_all_scores(response.text, year)
        print(f"  -> Processados {len(registros)} registros na memória.")
        
        # Acumula os dados em lista para o CSV
        flat_csv_data.extend(registros)
        
        # Constrói o dicionário aninhado para o JSON
        nested_json_data[year] = {}
        for reg in registros:
            disc = reg["disciplina"]
            hits = str(reg["acertos"]) # Convertemos acertos para string pois chaves de JSON são strings
            score = reg["escore"]
            
            if disc not in nested_json_data[year]:
                nested_json_data[year][disc] = {}
                
            nested_json_data[year][disc][hits] = score
            
    print("\nGerando arquivos JSON e CSV...")
    save_scores_to_csv(flat_csv_data, filename="data/escores_padronizados.csv")
    save_scores_to_json(nested_json_data, filename="data/escores_padronizados.json")
    
    print("Processo concluído com sucesso!")

if __name__ == "__main__":
    main()