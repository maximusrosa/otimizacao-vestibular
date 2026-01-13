from optimization import optimization
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
# from get_scores import getScores
# from get_ranking import getMinAC

app = FastAPI()

class UserData(BaseModel):
    course: str

    # Para otimização
    constraints: dict[str, list[str | int]]
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


'''
obs: para testar com essa instância, é preciso alterar a variável MIN_HITS em constants.py para 3

{
    "course": "Enfermagem",
    "min_AC": 622.42,
    "std_scores": {
        "PORT_RED": [317.14, 353.19, 389.25, 425.31, 461.37, 497.43, 533.49, 569.55, 605.61, 641.67, 677.73, 713.79, 749.85],
        "LIT":  [304.41, 343.08, 381.76, 420.44, 459.12, 497.80, 536.48, 575.16, 613.84, 652.51, 691.19, 729.87, 768.55],
        "HIS":  [308.41, 348.16, 387.90, 427.65, 467.39, 507.14, 546.88, 586.63, 626.38, 666.12, 705.87, 745.61, 785.36],   
        "GEO":  [336.01, 373.98, 411.96, 449.94, 487.91, 525.89, 563.87, 601.84, 639.82, 677.80, 715.77, 753.75, 791.72],
        "MAT":  [413.30, 443.40, 473.50, 503.61, 533.71, 563.81, 593.91, 624.01, 654.11, 684.21, 714.32, 744.42, 774.52],
        "LEM":  [367.35, 400.53, 433.70, 466.88, 500.05, 533.23, 566.40, 599.58, 632.75, 665.93, 699.10, 732.28, 765.45],
        "FIS":  [432.78, 478.14, 523.50, 568.86, 614.22, 659.57, 704.93, 750.29, 795.65, 841.00, 886.36, 931.72, 977.08],
        "QUI":  [419.11, 459.69, 500.26, 540.83, 581.41, 621.98, 662.56, 703.13, 743.71, 784.28, 824.86, 865.43, 906.01],
        "BIO":  [413.48, 450.16, 486.84, 523.51, 560.19, 596.87, 633.55, 670.23, 706.91, 743.58, 780.26, 816.94, 853.62]
    },
    "constraints": {
        "MAT": [">=", 10],
        "LEM": ["==", 12]
    },
    "min_subjects": ["BIO","QUI"]
}

'''