import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HomeView from './view';
import { MIN_HITS, MAX_HITS, SUBJECTS } from '../../constants';

const optimizationRoute = 'http://localhost:8000/optimize';

const MOCK_DATA = {
    course: "Enfermagem",
    min_AC: 622.42,
    std_scores: {
        "PORT_RED": [317.14, 353.19, 389.25, 425.31, 461.37, 497.43, 533.49, 569.55, 605.61, 641.67, 677.73, 713.79, 749.85, 785.91, 821.97],
        "LIT":  [304.41, 343.08, 381.76, 420.44, 459.12, 497.80, 536.48, 575.16, 613.84, 652.51, 691.19, 729.87, 768.55, 807.23, 845.91],
        "HIS":  [308.41, 348.16, 387.90, 427.65, 467.39, 507.14, 546.88, 586.63, 626.38, 666.12, 705.87, 745.61, 785.36, 825.11, 864.85],   
        "GEO":  [336.01, 373.98, 411.96, 449.94, 487.91, 525.89, 563.87, 601.84, 639.82, 677.80, 715.77, 753.75, 791.72, 829.69, 867.67],
        "MAT":  [413.30, 443.40, 473.50, 503.61, 533.71, 563.81, 593.91, 624.01, 654.11, 684.21, 714.32, 744.42, 774.52, 804.62, 834.72],
        "LEM":  [367.35, 400.53, 433.70, 466.88, 500.05, 533.23, 566.40, 599.58, 632.75, 665.93, 699.10, 732.28, 765.45, 798.62, 831.80],
        "FIS":  [432.78, 478.14, 523.50, 568.86, 614.22, 659.57, 704.93, 750.29, 795.65, 841.00, 886.36, 931.72, 977.08, 980.05, 992.41],
        "QUI":  [419.11, 459.69, 500.26, 540.83, 581.41, 621.98, 662.56, 703.13, 743.71, 784.28, 824.86, 865.43, 906.01, 946.59, 987.16],
        "BIO":  [413.48, 450.16, 486.84, 523.51, 560.19, 596.87, 633.55, 670.23, 706.91, 743.58, 780.26, 816.94, 853.62, 890.30, 926.98]
    }
};

function HomePage(){
    const navigate = useNavigate();
    
    // Estado do formulário
    const [course, setCourse] = useState(MOCK_DATA.course);
    const [year, setYear] = useState('');
    const [language, setLanguage] = useState('');
    const [accessForm, setAccessForm] = useState('');
    const [subjectsData, setSubjectsData] = useState(
      SUBJECTS.reduce((acc, subj) => ({
        ...acc,
        [subj.id]: { min: '', max: '', minimize: false }
      }), {})
    );

    // Atualiza os inputs da tabela
    const handleSubjectChange = (id, field, value) => {
      // Validação de intervalo para min e max
      if (field === 'min' || field === 'max') {
        // Permite limpar o campo (string vazia)
        if (value === '') {
            setSubjectsData(prev => ({
                ...prev,
                [id]: { ...prev[id], [field]: value }
            }));
            return;
        }

        const intValue = parseInt(value, 10);

        // Garante que é um número e está dentro do intervalo [1, 15]
        if (!isNaN(intValue) && intValue >= MIN_HITS && intValue <= MAX_HITS) {
             setSubjectsData(prev => ({
                ...prev,
                [id]: { ...prev[id], [field]: value }
            }));
        }
        // Se estiver fora do intervalo ou inválido, ignora a alteração (input controlado não muda)
      } else {
          setSubjectsData(prev => ({
            ...prev,
            [id]: {
              ...prev[id],
              [field]: value
            }
          }));
      }
    };

    const handleOptimize = async () => {
      // 1. Construir min_subjects
      const min_subjects = Object.entries(subjectsData)
        // Filtra matérias onde minimize está TRUE
        .filter(([_, data]) => data.minimize)
        .map(([id, _]) => id);

      // 2. Construir constraints
      const constraints = {};
      
      Object.entries(subjectsData).forEach(([id, data]) => {
        const subjectConstraints = [];
        if (data.min !== '') {
          subjectConstraints.push([">=", parseInt(data.min)]);
        } 
        if (data.max !== '') {
            subjectConstraints.push(["<=", parseInt(data.max)]);
        }
        
        if (subjectConstraints.length > 0) {
            constraints[id] = subjectConstraints;
        }
      });

      const payload = {
        course: course,
        constraints: constraints,
        min_subjects: min_subjects,
        // Enviando mock data pois o form não tem os scrapers ainda
        std_scores: MOCK_DATA.std_scores,
        min_AC: MOCK_DATA.min_AC,
      };

      console.log("Enviando Payload:", payload);

      try {
        const response = await fetch(optimizationRoute, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        console.log("Resultado Recebido:", result);

        navigate('/resultados', { state: { results: result } });
        
      } catch (error) {
        alert("Erro na otimização. Verifique se o backend está rodando.");
        console.error(error);
      }
    };
    
    // 2. Retorna a Visualização
    return (
        <HomeView 
            course={course}
            setCourse={(e) => setCourse(e.target.value)}
            year={year}
            setYear={(e) => setYear(e.target.value)}
            language={language}
            setLanguage={(e) => setLanguage(e.target.value)}
            accessForm={accessForm}
            setAccessForm={(e) => setAccessForm(e.target.value)}
            handleOptimize={handleOptimize}
            subjects={subjectsData}
            handleSubjectChange={handleSubjectChange}
        />
    );
}

export default HomePage;