from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from .utils import getGraphData
from .optimization import optimization
from .get_scores import get_scores
from .get_ranking import get_ranking, get_min_AC, get_available_courses
from .constants import FOREIGN_LANGUAGES, ENTRY_MODES

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def _log_validation_error(request: Request, exc: RequestValidationError):
    body = await request.body()
    print("=== 422 VALIDATION ERROR ===")
    print("errors:", exc.errors())
    print("raw body:", body.decode("utf-8", errors="replace"))
    return JSONResponse(status_code=422, content={"detail": exc.errors()})

# Configuração do CORS
origins = [
    "http://localhost:3000", # front-end
    "http://127.0.0.1:3000", # back-end
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite todos os métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"], # Permite todos os headers
)

class UserData(BaseModel):
    course: str

    # Para otimização
    constraints: dict[str, list[list[str | int]]]
    min_subjects: list[str]

    # Para web scraping
    foreign_language: str
    reference_year: str
    entry_method: str

# Define os campos que serão retornados para o front-end
class ReturnedData(BaseModel):
    result: dict
    graphJson: dict[int, float]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/courses", response_model=list[str])
def get_courses(reference_year: str):
    return get_available_courses(reference_year)


@app.get("/foreign-languages", response_model=list[str])
def get_foreign_languages():
    return FOREIGN_LANGUAGES


@app.get("/entry-modes", response_model=list[str])
def get_entry_modes():
    return ENTRY_MODES


@app.post("/optimize")
def optimize(user_data: UserData):
    std_scores = get_scores(user_data.reference_year, user_data.foreign_language)
    ranking = get_ranking(user_data.reference_year, user_data.course)
    min_AC = get_min_AC(ranking, user_data.entry_method)

    result = optimization(user_data.course, min_AC, std_scores, user_data.constraints, user_data.min_subjects)

    graphData = getGraphData(int(user_data.reference_year), user_data.course, user_data.entry_method)

    # Retorna o dicionário de atributos do objeto OptimizationResult para serialização JSON
    return ReturnedData(result=result.__dict__, graphJson=graphData)
