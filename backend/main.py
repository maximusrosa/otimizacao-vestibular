from optimization import optimization, OptimizationResult
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import utils
# from get_scores import getScores
from get_ranking import getRanking, getMinAC

app = FastAPI()

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
    #foreign_language: str
    reference_year: str
    entry_method: str

    # Dados obtidos por web scraping (não vão ficar aqui)
    std_scores: dict[str, list[float]]

# Define os campos que serão retornados para o front-end
class ReturnedData(BaseModel):
    result: dict
    graphJson: dict[int, float]


@app.post("/optimize")
def optimize(user_data: UserData):
    #std_scores = getScores(user_data.reference_year, user_data.foreign_language)

    ranking = getRanking(user_data.reference_year, user_data.course)
    min_AC = getMinAC(ranking, user_data.entry_method)

    # result = optimization(user_data.course, min_AC, std_scores, user_data.constraints, user_data.min_subjects)

    result = optimization(user_data.course, min_AC, user_data.std_scores, user_data.constraints, user_data.min_subjects)

    graphData = utils.getGraphData(int(user_data.reference_year), user_data.course, user_data.entry_method)
    
    # Retorna o dicionário de atributos do objeto OptimizationResult para serialização JSON
    return ReturnedData(result=result.__dict__, graphJson=graphData)