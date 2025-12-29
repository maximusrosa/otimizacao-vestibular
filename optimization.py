import pulp
import utils
from constants import *

# Objeto de retorno
class OptimizationResult:
    def __init__(self, chosen_hits: dict[str, dict[str, float]], AC: float, threshold: float, status: str):
        self.solve_status = status
        self.chosen_hits = chosen_hits
        self.AC = AC
        self.threshold = threshold


def add_constraints(model, x, constraints_dict: dict[str, tuple[str, int]]):
    for subject, (operator, value) in constraints_dict.items():
        if operator == ">=":
            model += pulp.lpSum(num_hits * x[subject][num_hits] 
                                for num_hits in range(MIN_HITS, MAX_HITS +1)) >= value, f"min_hits_{subject}"
        elif operator == "<=":
            model += pulp.lpSum(num_hits * x[subject][num_hits] 
                                for num_hits in range(MIN_HITS, MAX_HITS +1)) <= value, f"max_hits_{subject}"
        elif operator == "==":
            model += pulp.lpSum(num_hits * x[subject][num_hits] 
                                for num_hits in range(MIN_HITS, MAX_HITS +1)) == value, f"hits_{subject}"
        else:
            raise ValueError(f"Unknown operator {operator} for subject {subject}")
        

def optimization(course: str, min_AC: float, constraints_dict: dict[str, tuple[str, int]], 
                 std_score: dict[str, list[float]], min_subjects: list[str]=SUBJECTS) -> OptimizationResult:
    
    weights = utils.read_course_weights(course)
    
    total_weights = sum(weights[subject] for subject in SUBJECTS)

    # --------------- Model --------------------- #

    model = pulp.LpProblem("UFRGS_Vest_Optim", pulp.LpMinimize)

    # --------------- Variables ----------------- #

    x = {subject: {num_hits: pulp.LpVariable(f"x_{subject}_{num_hits}", cat="Binary") 
                for num_hits in range(MIN_HITS, MAX_HITS +1)} for subject in SUBJECTS}

    # Variáveis dos escores padronizados 
    EP_var = {subject: pulp.LpVariable(f"EP_{subject}", lowBound=1e-6) for subject in SUBJECTS}
    
    # Variáveis auxiliares, linearização da nota final
    y_var  = {subject: pulp.LpVariable(f"y_{subject}", lowBound=0) for subject in SUBJECTS}


    # --------------- Constraints -------------- #

    # Link EP and y
    for subject in SUBJECTS:
        # exactly one choice
        model += pulp.lpSum(x[subject][num_hits] for num_hits in range(MIN_HITS, MAX_HITS +1)) == 1, f"one_choice_{subject}"

        # EP definition (num_hits-3 because EP array is 0-indexed but num_hits starts at 3)
        model += EP_var[subject] == pulp.lpSum(std_score[subject][num_hits-MIN_HITS] * 
                                            x[subject][num_hits] for num_hits in range(MIN_HITS, MAX_HITS +1)), f"EP_def_{subject}"

        # y definition
        model += y_var[subject] == pulp.lpSum((1.0 / std_score[subject][num_hits-MIN_HITS]) *
                                            x[subject][num_hits] for num_hits in range(MIN_HITS, MAX_HITS +1)), f"y_def_{subject}"

    # Minimum AC
    model += pulp.lpSum(weights[subject] * y_var[subject] 
                        for subject in SUBJECTS) <= total_weights / min_AC, "min_AC"

    # Total hits >= 30% of all questions
    model += pulp.lpSum(num_hits * x[subject][num_hits] 
                        for subject in SUBJECTS for num_hits in range(MIN_HITS, MAX_HITS +1)) >= 41, "total_hits"
    
    # User-defined constraints
    add_constraints(model, x, constraints_dict)

    # --------------- Objective ------------------ #

    model += pulp.lpSum(EP_var[subject] for subject in min_subjects), "Min_sum_EPs"

    # -------------------------------------------- #

    # Solve
    solver = pulp.PULP_CBC_CMD(msg=True, timeLimit=60)
    model.solve(solver)
    
    # Output
    status = pulp.LpStatus[model.status]
    print("Solver status:", status)

    if status in ("Optimal","Optimal (Integer)","Feasible"):
        chosen = {}
        # y_val = 1/(EP_selecionado)
        y_vals = {}

        for subject in SUBJECTS:
            q_chosen = next(num_hits for num_hits in range(MIN_HITS, MAX_HITS +1) if pulp.value(x[subject][num_hits]) >= 1) # type: ignore
            ep_val = pulp.value(EP_var[subject])
            chosen[subject] = {"num_hits": q_chosen, "EP": ep_val}

            y_vals[subject] = pulp.value(y_var[subject])

        print("\nChosen EP values:")

        for subject,info in chosen.items():
            print(f" {subject:4s} -> HITS = {info['num_hits']:2d}, EP = {info['EP']:.4f}")

        sum_p_y = sum(weights[subject]*y_vals[subject] for subject in SUBJECTS)
        grade = total_weights/sum_p_y

        result = OptimizationResult(chosen, AC=grade, threshold=min_AC, status=status)

        print()
        print(f"nota = {grade:.6f} (limite {min_AC})")
        #print(f"\nSum p_i*y_i = {sum_p_y:.6f}")
        #print("Objective =", pulp.value(model.objective))
    else:
        print("No feasible solution.")
        result = OptimizationResult({}, AC=0.0, threshold=min_AC, status=status)

    return result

