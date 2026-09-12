from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Importando os scripts de otimização e utils originais
from .optimization import optimization, OptimizationResult
from .essay_scores import calculate_essay_standard_score, compose_port_red_scores
from .constants import MIN_APPROVED_ESSAY_SCORE, MIN_ESSAY_SCORE, MAX_ESSAY_SCORE

# Importando as novas funções de banco de dados
from . import database

# ==========================================
# LIFESPAN (STARTUP / SHUTDOWN)
# ==========================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    database.load_databases()
    print("API pronta para receber requisições!")
    
    yield
    
    # Roda ao desligar a API
    print("Encerrando API...")
    database.clear_databases()

# ==========================================
# CONFIGURAÇÃO DO APP
# ==========================================
app = FastAPI(lifespan=lifespan)

@app.exception_handler(RequestValidationError)
async def _log_validation_error(request: Request, exc: RequestValidationError):
    body = await request.body()
    print("=== 422 VALIDATION ERROR ===")
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# SCHEMAS
# ==========================================
class UserData(BaseModel):
    course: str
    constraints: dict[str, list[list[str | int]]]
    min_subjects: list[str]
    foreign_language: str
    reference_year: str
    entry_method: str
    essay_score: float = Field(..., ge=MIN_ESSAY_SCORE, le=MAX_ESSAY_SCORE)

class ReturnedData(BaseModel):
    result: dict
    graphJson: dict[int, float]

# ==========================================
# ROTAS
# ==========================================
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/data/status")
def data_status():
    return database.get_data_status()

@app.post("/optimize")
def optimize(user_data: UserData):
    # As funções do database entregam os dados na hora
    std_scores = database.get_scores_from_memory(
        user_data.reference_year, 
        user_data.foreign_language
    )
    
    min_AC = database.get_min_ac_from_memory(
        user_data.reference_year, 
        user_data.course, 
        user_data.entry_method
    )

    graphData = database.get_cutoff_graph_from_memory(
        int(user_data.reference_year),
        user_data.course,
        user_data.entry_method,
    )

    if user_data.essay_score < MIN_APPROVED_ESSAY_SCORE:
        return ReturnedData(
            result={
                "solve_status": "Eliminated",
                "chosen_hits": {},
                "AC": 0.0,
                "threshold": min_AC,
                "reason": f"Nota de redação abaixo do mínimo de {MIN_APPROVED_ESSAY_SCORE:g}.",
            },
            graphJson=graphData,
        )

    essay_stats = database.get_essay_stats_from_memory(user_data.reference_year)
    essay_ep = calculate_essay_standard_score(
        user_data.essay_score,
        essay_stats["mean"],
        essay_stats["std_dev"],
    )

    std_scores["PORT_RED"] = compose_port_red_scores(std_scores["PORT_RED"], essay_ep)

    result = optimization(
        user_data.course, 
        min_AC, 
        std_scores, 
        user_data.constraints, 
        user_data.min_subjects
    )

    result_dict = result.__dict__
    result_dict["essay"] = {
        "raw_score": user_data.essay_score,
        "standard_score": essay_ep,
        "mean": essay_stats["mean"],
        "std_dev": essay_stats["std_dev"],
    }
    result_dict["assumptions"] = [
        "O cálculo assume que o candidato foi pré-classificado conforme o edital."
    ]

    return ReturnedData(result=result_dict, graphJson=graphData)
