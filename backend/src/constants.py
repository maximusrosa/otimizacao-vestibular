from pathlib import Path


# Otimização
MIN_HITS = 1
MAX_HITS = 15
INF = float("inf")
SUBJECTS = ["BIO", "FIS", "QUI", "MAT", "HIS", "LIT", "PORT_RED", "LEM", "GEO"]


# Arquivos de dados
COURSE_WEIGHTS_PATH = str(Path(__file__).resolve().parent.parent / "data" / "course_weights.csv")
COURSE_MAPPING_PATH = str(Path(__file__).resolve().parent.parent / "data" / "course_mapping.json")


# Opções do formulário
YEARS = ["2022", "2023", "2024", "2025"]
FOREIGN_LANGUAGES = ["Inglês", "Espanhol", "Italiano", "Francês", "Alemão"]

# Mapeamento de regex para cada modalidade de ingresso
ENTRY_MODE_PATTERNS = {
    "AC": r"AC",
    "LI_EP": r"LI_EP",
    "LI_PPI": r"LI_PPI",
    "LB_EP": r"LB_EP",
    "LB_PPI": r"LB_PPI",
    "LI_PCD": r"LI_PCD",
    "LB_PCD": r"LB_PCD",
    "LI_Q": r"LI_Q",
    "LB_Q": r"LB_Q"
}

ENTRY_MODES = list(ENTRY_MODE_PATTERNS.keys())

# Web scraping
SCORES_URL = "https://www.ufrgs.br/vestibular/cv{year}/histogramas/"
RANKING_URL = "https://www1.ufrgs.br/PortalEnsino/GraduacaoProcessoSeletivo/index.php/DivulgacaoDadosChamamento"

# Mapeamento de regex para cada situação que conta para a nota de corte
STATUS_PATTERNS = {
    "Matriculado": r"Matriculado",
    "Lotado em vaga": r"Lotado em vaga",
    "Renunciante": r"Renunciante",
}

# Mapeamento do nome da disciplina no site para o código interno usado em SUBJECTS
SUBJECT_NAME_TO_CODE = {
    "Língua Portuguesa": "PORT_RED",
    "Literatura em Língua Portuguesa": "LIT",
    "História": "HIS",
    "Geografia": "GEO",
    "Matemática": "MAT",
    "Física": "FIS",
    "Química": "QUI",
    "Biologia": "BIO",
}
