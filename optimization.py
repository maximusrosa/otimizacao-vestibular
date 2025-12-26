import pulp

MIN_ACERTOS = 3
MAX_ACERTOS = 15

NOTA_LIMITE = 622.42

# --- Data: EP tables for num_hits = 3..15
std_score = {
    "PORT": [317.14, 353.19, 389.25, 425.31, 461.37, 497.43, 533.49, 569.55, 605.61, 641.67, 677.73, 713.79, 749.85],
    "LIT":  [304.41, 343.08, 381.76, 420.44, 459.12, 497.80, 536.48, 575.16, 613.84, 652.51, 691.19, 729.87, 768.55],
    "HIS":  [308.41, 348.16, 387.90, 427.65, 467.39, 507.14, 546.88, 586.63, 626.38, 666.12, 705.87, 745.61, 785.36],   
    "GEO":  [336.01, 373.98, 411.96, 449.94, 487.91, 525.89, 563.87, 601.84, 639.82, 677.80, 715.77, 753.75, 791.72],
    "MAT":  [413.30, 443.40, 473.50, 503.61, 533.71, 563.81, 593.91, 624.01, 654.11, 684.21, 714.32, 744.42, 774.52],
    "ING":  [367.35, 400.53, 433.70, 466.88, 500.05, 533.23, 566.40, 599.58, 632.75, 665.93, 699.10, 732.28, 765.45],
    "FIS":  [432.78, 478.14, 523.50, 568.86, 614.22, 659.57, 704.93, 750.29, 795.65, 841.00, 886.36, 931.72, 977.08],
    "QUI":  [419.11, 459.69, 500.26, 540.83, 581.41, 621.98, 662.56, 703.13, 743.71, 784.28, 824.86, 865.43, 906.01],
    "BIO":  [413.48, 450.16, 486.84, 523.51, 560.19, 596.87, 633.55, 670.23, 706.91, 743.58, 780.26, 816.94, 853.62],
}

# weights (Ciência da Computação)
weights = {
    "BIO": 1, "FIS": 2, "QUI": 1, "MAT": 3,
    "HIS": 1, "LIT": 1, "PORT": 3, "ING": 2, "GEO": 1
}

subjects = ["BIO","FIS","QUI","MAT","HIS","LIT","PORT","ING","GEO"]
total_weights = sum(weights[subject] for subject in subjects)

# --- Model ---
model = pulp.LpProblem("UFRGS_CIC_Optim", pulp.LpMinimize)

x = {subject: {num_hits: pulp.LpVariable(f"x_{subject}_{num_hits}", cat="Binary") 
               for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)} for subject in subjects}

EP_var = {subject: pulp.LpVariable(f"EP_{subject}", lowBound=1e-6) for subject in subjects}

y_var  = {subject: pulp.LpVariable(f"y_{subject}", lowBound=0) for subject in subjects}

# Link EP and y
for subject in subjects:
    # exactly one choice
    model += pulp.lpSum(x[subject][num_hits] for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)) == 1, f"one_choice_{subject}"

    # EP definition (num_hits-3 because EP array is 0-indexed but num_hits starts at 3)
    model += EP_var[subject] == pulp.lpSum(std_score[subject][num_hits-MIN_ACERTOS] * 
                                           x[subject][num_hits] for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)), f"EP_def_{subject}"

    # y definition
    model += y_var[subject] == pulp.lpSum((1.0 / std_score[subject][num_hits-MIN_ACERTOS]) *
                                           x[subject][num_hits] for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)), f"y_def_{subject}"

# nota constraint
model += pulp.lpSum(weights[subject] * y_var[subject] 
                    for subject in subjects) <= total_weights / NOTA_LIMITE, "NOTA_LIMITE"

# Total hits >= 30% of all questions
model += pulp.lpSum(num_hits * x[subject][num_hits] 
                    for subject in subjects for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)) >= 41, "total_hits"

#------------------------------- Subject-specific constraints ------------------------------------#

# Math must have exactly 12 hits
model += pulp.lpSum(num_hits * x["MAT"][num_hits] 
                    for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)) == 12, "hits_MATH"

# Portuguese must have exactly 13 hits
model += pulp.lpSum(num_hits * x["PORT"][num_hits] 
                    for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)) == 13, "hits_PORT"

# Literature must have exactly 13 hits
model += pulp.lpSum(num_hits * x["LIT"][num_hits] 
                    for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)) == 13, "hits_LIT"

# History must have exactly 9 hits
model += pulp.lpSum(num_hits * x["HIS"][num_hits] 
                    for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)) == 9, "hits_HIS"

# Chemistry must have exactly 8 hits
model += pulp.lpSum(num_hits * x["QUI"][num_hits] 
                    for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)) == 8, "hits_QUI"

# Geography must have exactly 3 hits
model += pulp.lpSum(num_hits * x["GEO"][num_hits] 
                    for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)) == 3, "hits_GEO"

# English must have exactly 13 hits
model += pulp.lpSum(num_hits * x["ING"][num_hits] 
                    for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1)) == 13, "hits_ING"

#-------------------------------------------------------------------------------------------------#

# Objective
model += pulp.lpSum(EP_var[subject] for subject in subjects), "Min_sum_EPs"

# Solve
solver = pulp.PULP_CBC_CMD(msg=True, timeLimit=60)
model.solve(solver)

# Output
status = pulp.LpStatus[model.status]
print("Solver status:", status)

if status in ("Optimal","Optimal (Integer)","Feasible"):
    chosen = {}

    for subject in subjects:
        q_chosen = next(num_hits for num_hits in range(MIN_ACERTOS, MAX_ACERTOS +1) if pulp.value(x[subject][num_hits]) >= 1) # type: ignore
        ep_val = pulp.value(EP_var[subject])
        y_val = pulp.value(y_var[subject])
        chosen[subject] = {"num_hits": q_chosen, "EP": ep_val, "y": y_val}

    print("\nChosen EP values:")

    for subject,info in chosen.items():
        print(f" {subject:4s} -> acertos = {info['num_hits']:2d}, EP = {info['EP']:.4f}")

    sum_p_y = sum(weights[subject]*chosen[subject]["y"] for subject in subjects)
    nota = total_weights/sum_p_y

    print()
    print(f"nota = {nota:.6f} (limite {NOTA_LIMITE})")
    #print(f"\nSum p_i*y_i = {sum_p_y:.6f}")
    #print("Objective =", pulp.value(model.objective))
else:
    print("No feasible solution.")