import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HomeView from './view';
import { MIN_HITS, MAX_HITS, SUBJECTS } from '../../constants';

const optimizationRoute = 'http://localhost:8000/optimize';
const coursesRoute = 'http://localhost:8000/courses';
const yearsRoute = 'http://localhost:8000/years';
const foreignLanguagesRoute = 'http://localhost:8000/foreign-languages';
const entryModesRoute = 'http://localhost:8000/entry-modes';

function HomePage(){
    const navigate = useNavigate();
    
    // Estado do formulário - Inicializado vazio para os selects dinâmicos
    const [course, setCourse] = useState('');
    const [referenceYear, setReferenceYear] = useState('');
    const [language, setLanguage] = useState('');
    const [entryMethod, setEntryMethod] = useState('');
    
    // Estado para as opções dos selects e loading
    const [yearOptions, setYearOptions] = useState([]);
    const [courseOptions, setCourseOptions] = useState([]);
    const [languageOptions, setLanguageOptions] = useState([]);
    const [entryMethodOptions, setEntryMethodOptions] = useState([]);
    const [isLoadingCourses, setIsLoadingCourses] = useState(false);
    const [isLoadingSelectionOptions, setIsLoadingSelectionOptions] = useState(false);
    
    const [subjectsData, setSubjectsData] = useState(
      SUBJECTS.reduce((acc, subj) => ({
        ...acc,
        [subj.id]: { min: MIN_HITS, max: MAX_HITS, minimize: false }
      }), {})
    );

    // Efeito para carregar Anos, Modalidades e Línguas Estrangeiras
    useEffect(() => {
      let isCancelled = false;

      const fetchSelectionOptions = async () => {
        setIsLoadingSelectionOptions(true);
        try {
          const [yearsResponse, languagesResponse, entryModesResponse] = await Promise.all([
            fetch(yearsRoute),
            fetch(foreignLanguagesRoute),
            fetch(entryModesRoute),
          ]);

          if (!yearsResponse.ok || !languagesResponse.ok || !entryModesResponse.ok) {
            throw new Error('Falha ao carregar opções de formulário');
          }

          const [fetchedYears, fetchedLanguages, fetchedEntryModes] = await Promise.all([
            yearsResponse.json(),
            languagesResponse.json(),
            entryModesResponse.json(),
          ]);

          if (!isCancelled) {
            setYearOptions(fetchedYears);
            setLanguageOptions(fetchedLanguages);
            setEntryMethodOptions(fetchedEntryModes);
          }
        } catch (error) {
          if (!isCancelled) {
            setYearOptions([]);
            setLanguageOptions([]);
            setEntryMethodOptions([]);
            alert('Erro ao carregar anos, línguas estrangeiras e formas de acesso.');
            console.error(error);
          }
        } finally {
          if (!isCancelled) {
            setIsLoadingSelectionOptions(false);
          }
        }
      };

      fetchSelectionOptions();
      return () => { isCancelled = true; };
    }, []);

    // Efeito para carregar Cursos quando o Ano de Referência muda
    useEffect(() => {
      if (!referenceYear) {
        setCourseOptions([]);
        return;
      }

      let isCancelled = false;

      const fetchCourses = async () => {
        setIsLoadingCourses(true);
        try {
          const response = await fetch(`${coursesRoute}?reference_year=${referenceYear}`);
          if (!response.ok) {
            throw new Error(`Falha ao buscar cursos: ${response.status}`);
          }

          const fetchedCourses = await response.json();
          if (!isCancelled) {
            setCourseOptions(fetchedCourses);
          }
        } catch (error) {
          if (!isCancelled) {
            setCourseOptions([]);
            alert("Erro ao carregar cursos. Verifique se o backend está rodando.");
            console.error(error);
          }
        } finally {
          if (!isCancelled) {
            setIsLoadingCourses(false);
          }
        }
      };

      fetchCourses();
      return () => { isCancelled = true; };
    }, [referenceYear]);

    // Atualiza os inputs da tabela de matérias
    const handleSubjectChange = (id, field, value) => {
      if (field === 'min' || field === 'max') {
        if (value === '') {
            setSubjectsData(prev => ({ ...prev, [id]: { ...prev[id], [field]: value } }));
            return;
        }

        const intValue = parseInt(value, 10);
        if (!isNaN(intValue) && intValue >= MIN_HITS && intValue <= MAX_HITS) {
             setSubjectsData(prev => ({ ...prev, [id]: { ...prev[id], [field]: value } }));
        }
      } else {
          setSubjectsData(prev => ({ ...prev, [id]: { ...prev[id], [field]: value } }));
      }
    };

    // Handler específico para o ano de referência (limpa o curso)
    const handleReferenceYearChange = (event) => {
      setReferenceYear(event.target.value);
      setCourse('');
    };

    const handleOptimize = async () => {
      // Validação do form implementada por você
      if (!referenceYear || !course || !language || !entryMethod) {
        alert('Selecione ano, curso, língua estrangeira e forma de acesso antes de otimizar.');
        return;
      }

      const minSubjects = Object.entries(subjectsData)
        .filter(([_, data]) => data.minimize)
        .map(([id, _]) => id);

      const constraints = {};
      Object.entries(subjectsData).forEach(([id, data]) => {
        const subjectConstraints = [];
        if (data.min !== '') subjectConstraints.push([">=", parseInt(data.min)]);
        if (data.max !== '') subjectConstraints.push(["<=", parseInt(data.max)]);
        
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
      };

      console.log("Enviando Payload:", JSON.stringify(payload, null, 2));

      try {
        const response = await fetch(optimizationRoute, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const result = await response.json();
        
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
    
    return (
        <HomeView 
            course={course}
            setCourse={(e) => setCourse(e.target.value)}
            referenceYear={referenceYear}
            setReferenceYear={handleReferenceYearChange}
            language={language}
            setLanguage={(e) => setLanguage(e.target.value)}
            entryMethod={entryMethod}
            setEntryMethod={(e) => setEntryMethod(e.target.value)}
            handleOptimize={handleOptimize}
            subjects={subjectsData}
            handleSubjectChange={handleSubjectChange}
            yearOptions={yearOptions}
            courseOptions={courseOptions}
            languageOptions={languageOptions}
            entryMethodOptions={entryMethodOptions}
            isCourseSelectionEnabled={Boolean(referenceYear) && !isLoadingCourses && courseOptions.length > 0}
            hasReferenceYearSelected={Boolean(referenceYear)}
            isLoadingCourses={isLoadingCourses}
            isLoadingSelectionOptions={isLoadingSelectionOptions}
        />
    );
}

export default HomePage;
