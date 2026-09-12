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
    
    // Estado do formulário
    const [course, setCourse] = useState(MOCK_DATA.course);
    const [referenceYear, setReferenceYear] = useState(MOCK_DATA.reference_year);
    const [language, setLanguage] = useState(MOCK_DATA.foreign_language);
    const [entryMethod, setEntryMethod] = useState(MOCK_DATA.entry_method);
    
    // NOVO: Estado para a nota da Redação (Iniciando com uma nota vazia ou 0)
    const [essayScore, setEssayScore] = useState(""); 
    
    const [subjectsData, setSubjectsData] = useState(
      SUBJECTS.reduce((acc, subj) => ({
        ...acc,
        [subj.id]: { min: MIN_HITS, max: MAX_HITS, minimize: false }
      }), {})
    );

    // Atualiza os inputs da tabela
    const handleSubjectChange = (id, field, value) => {
      if (field === 'min' || field === 'max') {
        if (value === '') {
            setSubjectsData(prev => ({
                ...prev,
                [id]: { ...prev[id], [field]: value }
            }));
            return;
        }

        const intValue = parseInt(value, 10);

        if (!isNaN(intValue) && intValue >= MIN_HITS && intValue <= MAX_HITS) {
             setSubjectsData(prev => ({
                ...prev,
                [id]: { ...prev[id], [field]: value }
            }));
        }
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
      // Validação da nota de redação antes de enviar
      const parsedEssayScore = parseFloat(essayScore);
      if (isNaN(parsedEssayScore)) {
          alert("Por favor, preencha uma nota válida para a Redação.");
          return;
      }

      // 1. Construir minSubjects
      const minSubjects = Object.entries(subjectsData)
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
        essay_score: parsedEssayScore, // NOVO: Campo obrigatório enviado no payload!
      };

      console.log("Enviando Payload:", JSON.stringify(payload, null, 2));

      try {
        const response = await fetch(optimizationRoute, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        // Trata erro de validação (422) ou outros erros HTTP amigavelmente
        if (!response.ok) {
            const errData = await response.json();
            console.error("Erro do servidor:", errData);
            alert("Erro na otimização. Verifique os dados enviados ou o console.");
            return;
        }
        
        const result = await response.json();
        console.log("Resultado Recebido:", result);

        navigate('/resultados', { 
          state: { 
            results: result.result,
            historicalData: result.graphJson 
          } 
        });
        
      } catch (error) {
        alert("Erro na requisição. Verifique se o backend está rodando.");
        console.error(error);
      }
    };
    
    // 3. Retorna a Visualização
    return (
        <HomeView 
            course={course}
            setCourse={(e) => setCourse(e.target.value)}
            referenceYear={referenceYear}
            setReferenceYear={(e) => setReferenceYear(e.target.value)}
            language={language}
            setLanguage={(e) => setLanguage(e.target.value)}
            entryMethod={entryMethod}
            setEntryMethod={(e) => setEntryMethod(e.target.value)}
            essayScore={essayScore}
            setEssayScore={(e) => setEssayScore(e.target.value)}
            handleOptimize={handleOptimize}
            subjects={subjectsData}
            handleSubjectChange={handleSubjectChange}
        />
    );
}

export default HomePage;