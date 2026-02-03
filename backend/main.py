from optimization import optimization
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
# from get_scores import getScores
# from get_ranking import getMinAC

app = FastAPI()

# Configuração do CORS
origins = [
    "http://localhost:3000", # Endereço do seu front-end React
    "http://127.0.0.1:3000",
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
    #reference_year: str
    #exam: str
    #entry_method: str

    # Dados obtidos por web scraping (não vão ficar aqui)
    std_scores: dict[str, list[float]]
    min_AC: float


@app.post("/optimize")
def optimize(user_data: UserData):
    #std_scores = getScores(user_data.reference_year)
    #min_AC = getMinAC(user_data.reference_year, user_data.exam, user_data.course, user_data.entry_method)

    # Chama a otimização passando os dados recebidos no corpo da requisição
    # result = optimization(user_data.course, min_AC, std_scores, user_data.constraints, user_data.min_subjects)

    result = optimization(user_data.course, user_data.min_AC, user_data.std_scores, user_data.constraints, user_data.min_subjects)
    
    # Retorna o dicionário de atributos do objeto OptimizationResult para serialização JSON
    return result.__dict__