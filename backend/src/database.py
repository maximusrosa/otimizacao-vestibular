import json
import re
from .constants import ENTRY_MODE_PATTERNS, STATUS_PATTERNS, ENTRY_MODES

# ==========================================
# VARIÁVEIS GLOBAIS DE MEMÓRIA
# ==========================================
DB_ESCORES = {}
DB_CUTOFFS = {}
DB_RANKINGS_COMPLETOS = []
DB_REDACAO_STATS = {}

# ==========================================
# FUNÇÕES DE STARTUP E SHUTDOWN
# ==========================================
def load_databases():
    """Carrega os tres conjuntos de dados e pre-calcula notas de corte."""
    global DB_ESCORES, DB_CUTOFFS, DB_RANKINGS_COMPLETOS, DB_REDACAO_STATS
    print("Iniciando carregamento dos dados para a memória...")

    # Carrega e PREPARA os Escores
    try:
        with open("data/escores_padronizados.json", "r", encoding="utf-8") as f:
            raw_scores = json.load(f)
            
        # Transforma o dict {"1": 300, "2": 320} em uma lista ordenada [300, 320] UMA ÚNICA VEZ
        for year, year_data in raw_scores.items():
            DB_ESCORES[year] = {}
            for disc, hits_dict in year_data.items():
                # Ordena e cria a lista de escores
                lista_ordenada = [hits_dict[str(h)] for h in sorted(map(int, hits_dict.keys()))]
                DB_ESCORES[year][disc] = lista_ordenada
                
        print(f" -> Escores carregados e ordenados! Anos: {list(DB_ESCORES.keys())}")
    except FileNotFoundError:
        print(" [AVISO] escores_padronizados.json não encontrado.")

    # Carrega estatísticas anuais da redação
    try:
        with open("data/redacao_stats.json", "r", encoding="utf-8") as f:
            DB_REDACAO_STATS = json.load(f)

        print(f" -> Estatísticas de redação carregadas! Anos: {list(DB_REDACAO_STATS.keys())}")
    except FileNotFoundError:
        print(" [AVISO] redacao_stats.json não encontrado.")

    # Carrega os Rankings e pré-calcula Notas de Corte
    try:
        with open("data/rankings_completos.json", "r", encoding="utf-8") as f:
            DB_RANKINGS_COMPLETOS = json.load(f)
            
        status_regex = re.compile("|".join(STATUS_PATTERNS.values()))
        mode_regexes = {mode: re.compile(pat) for mode, pat in ENTRY_MODE_PATTERNS.items()}
        
        for cand in DB_RANKINGS_COMPLETOS:
            ano = str(cand["ano"])
            curso = cand["curso"]
            nota = float(cand["nota_final"])
            modalidade = cand["modalidade"]
            situacao = cand["situacao"]
            
            if not status_regex.search(situacao):
                continue
                
            for mode, regex in mode_regexes.items():
                if regex.search(modalidade):
                    if ano not in DB_CUTOFFS: DB_CUTOFFS[ano] = {}
                    if curso not in DB_CUTOFFS[ano]: DB_CUTOFFS[ano][curso] = {}
                    if mode not in DB_CUTOFFS[ano][curso]: DB_CUTOFFS[ano][curso][mode] = float('inf')
                    
                    if nota < DB_CUTOFFS[ano][curso][mode]:
                        DB_CUTOFFS[ano][curso][mode] = nota
                    break

        print(" -> Notas de corte pré-calculadas com sucesso!")
        
    except FileNotFoundError:
        print(" [AVISO] rankings_completos.json não encontrado.")


def clear_databases():
    """Libera as estruturas globais durante o encerramento da API."""
    global DB_ESCORES, DB_CUTOFFS, DB_RANKINGS_COMPLETOS, DB_REDACAO_STATS
    DB_ESCORES.clear()
    DB_CUTOFFS.clear()
    DB_RANKINGS_COMPLETOS.clear()
    DB_REDACAO_STATS.clear()


# ==========================================
# FUNÇÕES DE CONSULTA O(1)
# ==========================================
def get_scores_from_memory(year: str, foreign_language: str) -> dict[str, list[float]]:
    """Apenas filtra a língua estrangeira e retorna as listas já prontas."""
    lem_code = f"LEM_{foreign_language.upper()}"
    
    if year not in DB_ESCORES:
        raise ValueError(f"Ano {year} não encontrado na base de escores.")
        
    ano_data = DB_ESCORES[year]
    std_scores = {}
    
    for disc, lista_escores in ano_data.items():
        if disc.startswith("LEM_"):
            if disc != lem_code:
                continue # Ignora as outras línguas
            disc_name = "LEM" # Renomeia a língua escolhida para o solver
        else:
            disc_name = disc
            
        std_scores[disc_name] = lista_escores # Já é a lista final!
        
    return std_scores

def get_min_ac_from_memory(year: str, course: str, entry_mode: str) -> float:
    try:
        nota = DB_CUTOFFS[year][course][entry_mode]
        if nota == float('inf'):
            raise ValueError
        return nota
    except (KeyError, ValueError):
        raise RuntimeError(f"Nenhuma nota de corte encontrada para {course} ({entry_mode}) em {year}.")


def get_essay_stats_from_memory(year: str) -> dict:
    """Retorna media e desvio da redacao necessarios para calcular seu EP."""
    try:
        stats = DB_REDACAO_STATS[year]
    except KeyError:
        raise RuntimeError(f"Nenhuma estatística de redação encontrada para {year}.")

    if stats["std_dev"] <= 0:
        raise RuntimeError(f"Desvio padrão inválido para a redação de {year}.")

    return stats


def get_data_status() -> dict[str, list[str]]:
    """Informa quais anos estao disponiveis em cada conjunto da base."""
    ranking_years = sorted({str(candidate["ano"]) for candidate in DB_RANKINGS_COMPLETOS}, key=int)
    return {
        "scores_years": sorted(DB_ESCORES.keys(), key=int),
        "ranking_years": ranking_years,
        "essay_years": sorted(DB_REDACAO_STATS.keys(), key=int),
    }


def get_cutoff_graph_from_memory(reference_year: int, course: str, entry_mode: str, years_back: int = 5) -> dict[int, float]:
    """Monta a serie historica usando as mesmas notas de corte da otimizacao."""
    graph_data = {}
    first_year = reference_year - years_back

    for year in range(first_year, reference_year + 1):
        year_data = DB_CUTOFFS.get(str(year), {})
        course_data = year_data.get(course, {})
        cutoff = course_data.get(entry_mode)
        if cutoff is not None and cutoff != float("inf"):
            graph_data[year] = cutoff

    return graph_data
