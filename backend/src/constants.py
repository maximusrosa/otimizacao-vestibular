MIN_HITS = 1
MAX_HITS = 15

SUBJECTS = ["BIO","FIS","QUI","MAT","HIS","LIT","PORT_RED","LEM","GEO"]

COURSE_WEIGHTS_PATH = "data/course_weights.csv"

ENTRY_MODES = ["AC", "LI_EP", "LI_PPI", "LB_EP", "LB_PPI", "LI_PCD", "LB_PCD", "LI_Q", "LB_Q"]

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

# Mapeamento de regex para cada situação que conta para a nota de corte
STATUS_PATTERNS = {
    "Matriculado": r"Matriculado",
    "Lotado em vaga": r"Lotado em vaga",
    "Renunciante": r"Renunciante",
}

INF = float('inf')

SCORES_URL = "https://www.ufrgs.br/vestibular/cv{year}/histogramas/"

RANKING_URL = "https://www1.ufrgs.br/PortalEnsino/GraduacaoProcessoSeletivo/index.php/DivulgacaoDadosChamamento"

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

# Línguas estrangeiras disponíveis no site; a escolhida vira o código "LEM"
FOREIGN_LANGUAGES = ["Inglês", "Espanhol", "Italiano", "Francês", "Alemão"]