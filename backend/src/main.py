from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator
from typing import Literal

# Importando os scripts de otimização e utils originais
from .optimization import optimization
from .essay_scores import build_essay_score_options
from .constants import ESSAY_SCORE_STEP, MIN_APPROVED_ESSAY_SCORE, MAX_ESSAY_SCORE

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
class EssayConstraints(BaseModel):
    """Faixa de notas brutas que pode ser escolhida para a Redação."""
    min: float = Field(MIN_APPROVED_ESSAY_SCORE, ge=MIN_APPROVED_ESSAY_SCORE, le=MAX_ESSAY_SCORE)
    max: float = Field(MAX_ESSAY_SCORE, ge=MIN_APPROVED_ESSAY_SCORE, le=MAX_ESSAY_SCORE)

    @model_validator(mode="after")
    def validate_range(self):
        if self.min > self.max:
            raise ValueError("Nota mínima da redação não pode superar a máxima.")
        if any(abs(value * 10 - round(value * 10)) > 1e-9 for value in (self.min, self.max)):
            raise ValueError("Os limites da redação devem usar no máximo uma casa decimal.")
        return self


class UserData(BaseModel):
    """Dados necessarios para compor os escores e executar o solver."""
    course: str
    constraints: dict[str, list[list[str | int]]]
    min_subjects: list[str]
    foreign_language: str
    reference_year: str
    entry_method: str
    essay_constraints: EssayConstraints = Field(default_factory=EssayConstraints)
    port_red_objective: Literal["none", "portuguese", "essay", "combined"] = "none"

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
    # Os escores objetivos ja estao em memoria e cada posicao representa uma
    # escolha inteira entre 1 e 15 acertos para a respectiva prova.
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

    essay_stats = database.get_essay_stats_from_memory(user_data.reference_year)
    essay_options = build_essay_score_options(
        user_data.essay_constraints.min,
        user_data.essay_constraints.max,
        essay_stats["mean"],
        essay_stats["std_dev"],
    )

    result = optimization(
        user_data.course, 
        min_AC, 
        std_scores, 
        user_data.constraints, 
        user_data.min_subjects,
        essay_options,
        user_data.port_red_objective,
    )

    result_dict = result.__dict__
    selected_port_red = result.chosen_hits.get("PORT_RED", {})
    result_dict["essay"] = {
        "raw_score": selected_port_red.get("essay_score"),
        "standard_score": selected_port_red.get("essay_EP"),
        "mean": essay_stats["mean"],
        "std_dev": essay_stats["std_dev"],
        "minimum": user_data.essay_constraints.min,
        "maximum": user_data.essay_constraints.max,
        "step": ESSAY_SCORE_STEP,
    }
    result_dict["port_red_objective"] = user_data.port_red_objective
    result_dict["assumptions"] = [
        "O cálculo assume que o candidato foi pré-classificado conforme o edital."
    ]

    return ReturnedData(result=result_dict, graphJson=graphData)
