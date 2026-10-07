import json
import os

from .constants import DATA_DIR, RANKING_MIN_DETAIL_YEAR
from .ranking_repository import repository as ranking_repository

# ==========================================
# VARIÁVEIS GLOBAIS DE MEMÓRIA
# ==========================================
DB_ESCORES = {}
DB_REDACAO_STATS = {}

# ==========================================
# FUNÇÕES DE STARTUP E SHUTDOWN
# ==========================================
def load_databases():
    """Carrega dados anuais em memória e inicializa o ranking persistente."""
    global DB_ESCORES, DB_REDACAO_STATS
    print("Iniciando carregamento dos dados para a memória...")
    DB_ESCORES = {}
    DB_REDACAO_STATS = {}

    # Carrega e PREPARA os Escores
    try:
        with open(DATA_DIR / "escores_padronizados.json", "r", encoding="utf-8") as f:
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
        with open(DATA_DIR / "redacao_stats.json", "r", encoding="utf-8") as f:
            DB_REDACAO_STATS = json.load(f)

        print(f" -> Estatísticas de redação carregadas! Anos: {list(DB_REDACAO_STATS.keys())}")
    except FileNotFoundError:
        print(" [AVISO] redacao_stats.json não encontrado.")

    ranking_repository.initialize(DATA_DIR / "rankings_completos.json")
    print(" -> Banco persistente de rankings inicializado.")


def clear_databases():
    """Libera as estruturas globais durante o encerramento da API."""
    global DB_ESCORES, DB_REDACAO_STATS
    DB_ESCORES.clear()
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
    return ranking_repository.get_cutoff(year, course, entry_mode)


def get_essay_stats_from_memory(year: str) -> dict:
    """Retorna media e desvio da redacao necessarios para calcular seu EP."""
    try:
        stats = DB_REDACAO_STATS[year]
    except KeyError:
        raise RuntimeError(f"Nenhuma estatística de redação encontrada para {year}.")

    if stats["std_dev"] <= 0:
        raise RuntimeError(f"Desvio padrão inválido para a redação de {year}.")

    return stats


def get_data_status() -> dict:
    """Informa quais anos estao disponiveis em cada conjunto da base."""
    status = {
        "scores_years": sorted(DB_ESCORES.keys(), key=int),
        "ranking_years": sorted(ranking_repository.available_years(), key=int),
        "detailed_ranking_years": sorted(ranking_repository.available_years(detailed_only=True), key=int),
        "essay_years": sorted(DB_REDACAO_STATS.keys(), key=int),
        "ranking_sync_enabled": os.environ.get("RANKING_SYNC_ENABLED", "false").lower() == "true",
        "ranking_sync_years": [
            year.strip() for year in os.environ.get("RANKING_SYNC_YEARS", "2025").split(",") if year.strip()
        ],
        "ranking_sync_time": os.environ.get("RANKING_SYNC_TIME", "05:00"),
        "ranking_sync_timezone": os.environ.get("TZ", "America/Sao_Paulo"),
    }
    status.update(ranking_repository.status())
    return status


def get_available_years() -> list[str]:
    """Retorna somente anos completos, prontos para uma otimização consistente."""
    ranking_years = {
        year for year in ranking_repository.available_years() if int(year) >= RANKING_MIN_DETAIL_YEAR
    }
    complete_years = set(DB_ESCORES) & ranking_years & set(DB_REDACAO_STATS)
    return sorted(complete_years, key=int, reverse=True)


def get_courses_from_memory(year: str) -> list[str]:
    """Lista os cursos que possuem ao menos uma nota de corte no ano informado."""
    return ranking_repository.courses(year)


def get_cutoff_graph_from_memory(reference_year: int, course: str, entry_mode: str, years_back: int = 5) -> dict[int, float]:
    """Monta a série histórica a partir do último estado confirmado no SQLite."""
    return ranking_repository.cutoff_graph(reference_year, course, entry_mode, years_back)


def get_candidate_window(
    year: int,
    course: str,
    entry_mode: str | None,
    anchor_score: float | None,
    offset: int | None,
    limit: int,
) -> dict:
    return ranking_repository.candidate_window(
        year,
        course,
        entry_mode=entry_mode,
        anchor_score=anchor_score,
        offset=offset,
        limit=limit,
    )
