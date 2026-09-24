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
    weights = utils.readCourseWeights(course)
    if not weights:
        raise RuntimeError(f"Pesos não encontrados para o curso {course}.")
    if port_red_objective not in PORT_RED_OBJECTIVES:
        raise ValueError(f"Objetivo de Português/Redação inválido: {port_red_objective}.")
    if PORT_RED in min_subjects:
        raise ValueError("Use port_red_objective para minimizar Português, Redação ou a nota conjunta.")

    missing_subjects = set(SUBJECTS) - set(std_scores)
    extra_subjects = set(std_scores) - set(SUBJECTS)
    if missing_subjects or extra_subjects:
        raise ValueError(
            f"Conjunto de disciplinas inválido. Ausentes: {sorted(missing_subjects)}; extras: {sorted(extra_subjects)}."
        )
    unknown_min_subjects = set(min_subjects) - set(REGULAR_SUBJECTS)
    if unknown_min_subjects:
        raise ValueError(f"Disciplinas inválidas na função objetivo: {sorted(unknown_min_subjects)}.")

    expected_score_count = MAX_HITS - MIN_HITS + 1
    for subject, scores in std_scores.items():
        if len(scores) != expected_score_count:
            raise ValueError(f"{subject} deve ter {expected_score_count} escores padronizados.")
        if any(score <= 0 for score in scores):
            raise ValueError(f"{subject} possui escore padronizado menor ou igual a zero.")
    if not essay_options:
        raise ValueError("Ao menos uma nota de redação deve ser oferecida ao solver.")

    # Cada par contem tudo que o modelo precisa como constante. Isso evita o
    # termo nao linear 1 / (EP_PORT + EP_RED) durante a otimizacao.
    port_red_options = {}
    for hits in range(MIN_HITS, MAX_HITS + 1):
        portuguese_ep = std_scores[PORT_RED][hits - MIN_HITS]
        for essay_index, essay in enumerate(essay_options):
            combined_ep = compose_port_red_score(portuguese_ep, essay["standard_score"])
            if combined_ep <= 0:
                raise ValueError("A combinação de Português e Redação gerou EP menor ou igual a zero.")
            port_red_options[(hits, essay_index)] = {
                "portuguese_ep": portuguese_ep,
                "essay_score": essay["raw_score"],
                "essay_ep": essay["standard_score"],
                "combined_ep": combined_ep,
            }

    total_weights = sum(weights[subject] for subject in SUBJECTS)
    model = pulp.LpProblem("UFRGS_Vest_Optim", pulp.LpMinimize)

    x = {
        subject: {
            hits: pulp.LpVariable(f"x_{subject}_{hits}", cat="Binary")
            for hits in range(MIN_HITS, MAX_HITS + 1)
        }
        for subject in REGULAR_SUBJECTS
    }
    z = {
        option: pulp.LpVariable(f"z_PORT_RED_{option[0]}_{option[1]}", cat="Binary")
        for option in port_red_options
    }

    hit_expressions = {}
    ep_expressions = {}
    reciprocal_expressions = {}

    for subject in REGULAR_SUBJECTS:
        model += pulp.lpSum(x[subject].values()) == 1, f"one_choice_{subject}"
        hit_expressions[subject] = pulp.lpSum(hits * x[subject][hits] for hits in x[subject])
        ep_expressions[subject] = pulp.lpSum(
            std_scores[subject][hits - MIN_HITS] * x[subject][hits] for hits in x[subject]
        )
        reciprocal_expressions[subject] = pulp.lpSum(
            (1.0 / std_scores[subject][hits - MIN_HITS]) * x[subject][hits] for hits in x[subject]
        )

    model += pulp.lpSum(z.values()) == 1, "one_choice_PORT_RED"
    hit_expressions[PORT_RED] = pulp.lpSum(option[0] * variable for option, variable in z.items())
    portuguese_ep_expression = pulp.lpSum(
        port_red_options[option]["portuguese_ep"] * variable for option, variable in z.items()
    )
    essay_ep_expression = pulp.lpSum(
        port_red_options[option]["essay_ep"] * variable for option, variable in z.items()
    )
    ep_expressions[PORT_RED] = pulp.lpSum(
        port_red_options[option]["combined_ep"] * variable for option, variable in z.items()
    )
    reciprocal_expressions[PORT_RED] = pulp.lpSum(
        (1.0 / port_red_options[option]["combined_ep"]) * variable for option, variable in z.items()
    )

    model += (
        pulp.lpSum(weights[subject] * reciprocal_expressions[subject] for subject in SUBJECTS)
        <= total_weights / min_AC,
        "min_AC",
    )
    model += pulp.lpSum(hit_expressions.values()) >= 41, "total_hits"
    add_hit_constraints(model, hit_expressions, constraints_dict)

    objective_terms = [ep_expressions[subject] for subject in min_subjects]
    if port_red_objective == "portuguese":
        objective_terms.append(portuguese_ep_expression)
    elif port_red_objective == "essay":
        objective_terms.append(essay_ep_expression)
    elif port_red_objective == "combined":
        objective_terms.append(ep_expressions[PORT_RED])
    model += pulp.lpSum(objective_terms), "Min_selected_EPs"

    model.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=60))
    status = pulp.LpStatus[model.status]
    if status not in ("Optimal", "Optimal (Integer)", "Feasible"):
        return OptimizationResult({}, AC=0.0, threshold=min_AC, status=status)

    chosen = {}
    reciprocal_values = {}
    for subject in REGULAR_SUBJECTS:
        selected_hits = next(hits for hits, variable in x[subject].items() if pulp.value(variable) >= 0.5)
        selected_ep = std_scores[subject][selected_hits - MIN_HITS]
        chosen[subject] = {"num_hits": selected_hits, "EP": selected_ep}
        reciprocal_values[subject] = 1.0 / selected_ep

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

    weighted_reciprocal_sum = sum(weights[subject] * reciprocal_values[subject] for subject in SUBJECTS)
    grade = round(total_weights / weighted_reciprocal_sum, 2)
    return OptimizationResult(chosen, AC=grade, threshold=min_AC, status=status)
