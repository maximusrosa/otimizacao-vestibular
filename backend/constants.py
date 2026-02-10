MIN_HITS = 1
MAX_HITS = 15

SUBJECTS = ["BIO","FIS","QUI","MAT","HIS","LIT","PORT_RED","LEM","GEO"]

COURSE_WEIGHTS_PATH = "../data/course_weights.csv"

ENTRY_MODES = ["AC", "LI_EP", "LI_PPI", "LB_EP", "LB_PPI", "LI_PCD", "LB_PCD", "LI_Q", "LB_Q"]

# Mapeamento de regex para cada modalidade de ingresso
MODE_PATTERNS = {
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

INF = float('inf')