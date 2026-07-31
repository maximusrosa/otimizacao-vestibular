import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HomeView from './view';
import { MIN_HITS, MAX_HITS, SUBJECTS } from '../../constants';

const optimizationRoute = 'http://localhost:8000/optimize';

const MOCK_DATA = {
    course: "Ciência da Computação - Bacharelado",
    reference_year: "2025",
    entry_method: "LI_EP",
    foreign_language: "Inglês",
};

function HomePage(){
    const navigate = useNavigate();
    
    // Estado do formulário - inicializado com valores de teste
    const [course, setCourse] = useState(MOCK_DATA.course);
    const [referenceYear, setReferenceYear] = useState(MOCK_DATA.reference_year);
    const [language, setLanguage] = useState(MOCK_DATA.foreign_language);
    const [entryMethod, setEntryMethod] = useState(MOCK_DATA.entry_method);
    const [subjectsData, setSubjectsData] = useState(
      SUBJECTS.reduce((acc, subj) => ({
        ...acc,
        [subj.id]: { min: MIN_HITS, max: MAX_HITS, minimize: false }
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
      // 1. Construir minSubjects
      const minSubjects = Object.entries(subjectsData)
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
        min_subjects: minSubjects,
        foreign_language: language,
        reference_year: referenceYear,
        entry_method: entryMethod,
        // Enviando mock data pois o form não tem os scrapers ainda
        std_scores: MOCK_DATA.std_scores,
      };

      console.log("Enviando Payload:", JSON.stringify(payload, null, 2));

      try {
        const response = await fetch(optimizationRoute, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        console.log("Resultado Recebido:", result);
        console.log("Dados do gráfico (notas de corte histórico):", result.graphJson);

        navigate('/resultados', { 
          state: { 
            results: result.result,
            historicalData: result.graphJson 
          } 
        });
        
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
            reference_year={referenceYear}
            setReferenceYear={(e) => setReferenceYear(e.target.value)}
            language={language}
            setLanguage={(e) => setLanguage(e.target.value)}
            entryMethod={entryMethod}
            setEntryMethod={(e) => setEntryMethod(e.target.value)}
            handleOptimize={handleOptimize}
            subjects={subjectsData}
            handleSubjectChange={handleSubjectChange}
        />
    );
}

export default HomePage;