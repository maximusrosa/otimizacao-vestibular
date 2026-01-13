from constants import COURSE_WEIGHTS_PATH

def readCourseWeights(course):
    with open(COURSE_WEIGHTS_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # Lê o cabeçalho (primeira linha) para obter os nomes das disciplinas
        header = lines[0].strip().split(',')
        subjects = header[1:]  # Ignora a primeira coluna (Curso)
        
        # Procura a linha do curso especificado
        for line in lines[1:]:
            data = line.strip().split(',')
            course_name = data[0]
            
            if course_name.startswith(course):
                weights = data[1:]  # Pega os pesos (ignora o nome do curso)
                # Retorna dicionário {disciplina: peso}
                return {subjects[i]: int(weights[i]) for i in range(len(subjects))}
        
        # Se o curso não for encontrado, retorna dicionário vazio
        return {}