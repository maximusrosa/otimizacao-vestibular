"""Modelo linear inteiro para as provas objetivas e a Redacao discretizada."""

import pulp

from .constants import MAX_HITS, MIN_HITS, PORT_RED_OBJECTIVES, SUBJECTS
from .essay_scores import compose_port_red_score
from .scripts import utils


PORT_RED = "PORT_RED"
REGULAR_SUBJECTS = [subject for subject in SUBJECTS if subject != PORT_RED]


class OptimizationResult:
    def __init__(self, chosen_hits: dict[str, dict[str, float]], AC: float, threshold: float, status: str):
        self.solve_status = status
        self.chosen_hits = chosen_hits
        self.AC = AC
        self.threshold = threshold


def add_hit_constraints(model, hit_expressions: dict, constraints_dict: dict[str, list[list[str | int]]]):
    """Aplica limites de acertos usando uma expressao por prova objetiva."""
    unknown_subjects = set(constraints_dict) - set(hit_expressions)
    if unknown_subjects:
        raise ValueError(f"Restrições para disciplinas desconhecidas: {sorted(unknown_subjects)}.")

    for subject, constraints in constraints_dict.items():
        for index, (operator, value) in enumerate(constraints):
            if operator == ">=":
                model += hit_expressions[subject] >= value, f"min_hits_{subject}_{index}"
            elif operator == "<=":
                model += hit_expressions[subject] <= value, f"max_hits_{subject}_{index}"
            else:
                raise ValueError(f"Operador desconhecido {operator} para {subject}.")

def optimization(
    course: str,
    min_AC: float,
    std_scores: dict[str, list[float]],
    constraints_dict: dict[str, list[list[str | int]]],
    min_subjects: list[str],
    essay_options: list[dict[str, float]],
    port_red_objective: str = "none",
) -> OptimizationResult:
    """Encontra acertos inteiros e uma nota de Redacao em passos de 0,1."""
    
    # Busca os pesos específicos do curso para o cálculo da média harmônica
    weights = utils.readCourseWeights(course)
    if not weights:
        raise RuntimeError(f"Pesos não encontrados para o curso {course}.")
        
    # Validações de integridade dos parâmetros fornecidos
    if port_red_objective not in PORT_RED_OBJECTIVES:
        raise ValueError(f"Objetivo de Português/Redação inválido: {port_red_objective}.")
    if PORT_RED in min_subjects:
        raise ValueError("Use port_red_objective para minimizar Português, Redação ou a nota conjunta.")

    # Verifica se as matérias fornecidas batem perfeitamente com as exigidas no vestibular
    missing_subjects = set(SUBJECTS) - set(std_scores)
    extra_subjects = set(std_scores) - set(SUBJECTS)
    if missing_subjects or extra_subjects:
        raise ValueError(
            f"Conjunto de disciplinas inválido. Ausentes: {sorted(missing_subjects)}; extras: {sorted(extra_subjects)}."
        )
        
    # Valida se as disciplinas marcadas para minimizar realmente existem
    unknown_min_subjects = set(min_subjects) - set(REGULAR_SUBJECTS)
    if unknown_min_subjects:
        raise ValueError(f"Disciplinas inválidas na função objetivo: {sorted(unknown_min_subjects)}.")

    # Verifica se os escores padronizados contêm exatamente 15 notas (1 a 15 acertos)
    expected_score_count = MAX_HITS - MIN_HITS + 1
    for subject, scores in std_scores.items():
        if len(scores) != expected_score_count:
            raise ValueError(f"{subject} deve ter {expected_score_count} escores padronizados.")
        if any(score <= 0 for score in scores):
            raise ValueError(f"{subject} possui escore padronizado menor ou igual a zero.")
            
    # Garante que o solver tenha pelo menos uma nota de redação para trabalhar
    if not essay_options:
        raise ValueError("Ao menos uma nota de redação deve ser oferecida ao solver.")

    # ==========================================
    # PREPARAÇÃO: PORTUGUÊS + REDAÇÃO
    # ==========================================
    # O solver linear (PuLP) não consegue lidar com divisões de variáveis (ex: 1 / (x + y)).
    # Para calcular a média harmônica de forma linear, pré-calculamos TODAS as combinações 
    # possíveis de acertos de Português com as notas de Redação fornecidas.
    # Nesse caso, as notas de redação fornecidas estão com passos de 0,1 e vão de 4,5 a 15.
    port_red_options = {}
    for hits in range(MIN_HITS, MAX_HITS + 1):
        portuguese_ep = std_scores[PORT_RED][hits - MIN_HITS]
        for essay_index, essay in enumerate(essay_options):
            combined_ep = compose_port_red_score(portuguese_ep, essay["standard_score"])
            if combined_ep <= 0:
                raise ValueError("A combinação de Português e Redação gerou EP menor ou igual a zero.")
            
            # A chave é a tupla (acertos_portugues, indice_da_redacao)
            port_red_options[(hits, essay_index)] = {
                "portuguese_ep": portuguese_ep,
                "essay_score": essay["raw_score"],
                "essay_ep": essay["standard_score"],
                "combined_ep": combined_ep,
            }

    # Soma total dos pesos do curso
    total_weights = sum(weights[subject] for subject in SUBJECTS)
    
    # Instancia o modelo matemático como um problema de MINIMIZAÇÃO
    model = pulp.LpProblem("UFRGS_Vest_Optim", pulp.LpMinimize)

    # ==========================================
    # VARIÁVEIS DE DECISÃO BINÁRIAS
    # ==========================================
    # Matriz 'x': 1 se a disciplina teve 'hits' acertos, 0 caso contrário
    x = {
        subject: {
            hits: pulp.LpVariable(f"x_{subject}_{hits}", cat="Binary")
            for hits in range(MIN_HITS, MAX_HITS + 1)
        }
        for subject in REGULAR_SUBJECTS
    }
    
    # Matriz 'z': 1 se a combinação (acertos_port, nota_redacao) foi escolhida, 0 caso contrário
    z = {
        option: pulp.LpVariable(f"z_PORT_RED_{option[0]}_{option[1]}", cat="Binary")
        for option in port_red_options
    }

    # Dicionários para acumular as expressões lineares do modelo
    hit_expressions = {}
    ep_expressions = {}
    reciprocal_expressions = {}

    # ==========================================
    # RESTRIÇÕES: DISCIPLINAS REGULARES
    # ==========================================
    for subject in REGULAR_SUBJECTS:
        # Garante que APENAS UM número de acertos seja escolhido por disciplina (soma das binárias = 1)
        model += pulp.lpSum(x[subject].values()) == 1, f"one_choice_{subject}"
        
        # Mapeia a soma algébrica dos acertos (ex: 1*x_1 + 2*x_2 ... 15*x_15)
        hit_expressions[subject] = pulp.lpSum(hits * x[subject][hits] for hits in x[subject])
        
        # Mapeia a soma algébrica dos escores padronizados (EP)
        ep_expressions[subject] = pulp.lpSum(
            std_scores[subject][hits - MIN_HITS] * x[subject][hits] for hits in x[subject]
        )
        
        # Mapeia a soma algébrica dos inversos (1 / EP) para calcular a média harmônica depois
        reciprocal_expressions[subject] = pulp.lpSum(
            (1.0 / std_scores[subject][hits - MIN_HITS]) * x[subject][hits] for hits in x[subject]
        )

    # ==========================================
    # RESTRIÇÕES: PORTUGUÊS + REDAÇÃO
    # ==========================================
    # Garante que APENAS UMA combinação de (Português + Redação) seja escolhida
    model += pulp.lpSum(z.values()) == 1, "one_choice_PORT_RED"
    
    # Acertos de português (pegando a posição 0 da tupla 'option')
    hit_expressions[PORT_RED] = pulp.lpSum(option[0] * variable for option, variable in z.items())
    
    # Isolando os EP's caso o usuário queira minimizar apenas a Redação ou apenas o Português
    portuguese_ep_expression = pulp.lpSum(
        port_red_options[option]["portuguese_ep"] * variable for option, variable in z.items()
    )
    essay_ep_expression = pulp.lpSum(
        port_red_options[option]["essay_ep"] * variable for option, variable in z.items()
    )
    
    # EP combinado (Português + Redação) final e seu inverso (1 / EP)
    ep_expressions[PORT_RED] = pulp.lpSum(
        port_red_options[option]["combined_ep"] * variable for option, variable in z.items()
    )
    reciprocal_expressions[PORT_RED] = pulp.lpSum(
        (1.0 / port_red_options[option]["combined_ep"]) * variable for option, variable in z.items()
    )

    # ==========================================
    # RESTRIÇÃO PRINCIPAL (NOTA DE CORTE) E REGRAS
    # ==========================================
    # Média Harmônica Ponderada >= min_AC
    # Matematicamente linearizado como: sum(Peso * (1/EP)) <= Total_Pesos / min_AC
    model += (
        pulp.lpSum(weights[subject] * reciprocal_expressions[subject] for subject in SUBJECTS)
        <= total_weights / min_AC,
        "min_AC",
    )
    
    # Regra do vestibular: O candidato precisa acertar no mínimo 30% das questões totais (41 acertos)
    model += pulp.lpSum(hit_expressions.values()) >= 41, "total_hits"
    
    # Aplica as restrições definidas pelo usuário (ex: "Quero acertar no mínimo 10 em Matemática")
    add_hit_constraints(model, hit_expressions, constraints_dict)

    # ==========================================
    # FUNÇÃO OBJETIVO
    # ==========================================
    # Coleta as expressões de EP das matérias que o usuário pediu para minimizar
    objective_terms = [ep_expressions[subject] for subject in min_subjects]
    
    # Adiciona a regra de minimização específica escolhida para Português/Redação
    if port_red_objective == "portuguese":
        objective_terms.append(portuguese_ep_expression)
    elif port_red_objective == "essay":
        objective_terms.append(essay_ep_expression)
    elif port_red_objective == "combined":
        objective_terms.append(ep_expressions[PORT_RED])
        
    # Instrui o modelo a encontrar o menor valor possível para a soma dessas matérias
    model += pulp.lpSum(objective_terms), "Min_selected_EPs"

    # ==========================================
    # EXECUÇÃO DO SOLVER
    # ==========================================
    # Roda o solver CBC (backend em C) sem mensagens no terminal e limite de 60 segundos
    model.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=60))
    status = pulp.LpStatus[model.status]
    
    # Se o solver não achar solução factível (ex: exigiu 15 acertos em tudo mas o limite não bate)
    if status not in ("Optimal", "Optimal (Integer)", "Feasible"):
        return OptimizationResult({}, AC=0.0, threshold=min_AC, status=status)

    # ==========================================
    # EXTRAÇÃO DOS RESULTADOS
    # ==========================================
    chosen = {}
    reciprocal_values = {}
    
    # Extrai o número de acertos das disciplinas regulares (onde a variável binária ficou >= 0.5)
    for subject in REGULAR_SUBJECTS:
        selected_hits = next(hits for hits, variable in x[subject].items() if pulp.value(variable) >= 0.5)
        selected_ep = std_scores[subject][selected_hits - MIN_HITS]
        
        chosen[subject] = {"num_hits": selected_hits, "EP": selected_ep}
        reciprocal_values[subject] = 1.0 / selected_ep

    # Extrai a combinação vencedora de Português + Redação
    selected_option = next(option for option, variable in z.items() if pulp.value(variable) >= 0.5)
    selected_port_red = port_red_options[selected_option]
    
    chosen[PORT_RED] = {
        "num_hits": selected_option[0],
        "EP": selected_port_red["combined_ep"],
        "portuguese_EP": selected_port_red["portuguese_ep"],
        "essay_score": selected_port_red["essay_score"],
        "essay_EP": selected_port_red["essay_ep"],
    }
    reciprocal_values[PORT_RED] = 1.0 / selected_port_red["combined_ep"]

    # Calcula a nota final (AC) exata do candidato com base nos escores selecionados
    weighted_reciprocal_sum = sum(weights[subject] * reciprocal_values[subject] for subject in SUBJECTS)
    grade = round(total_weights / weighted_reciprocal_sum, 2)
    
    return OptimizationResult(chosen, AC=grade, threshold=min_AC, status=status)