import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HomeView from './view';
import { MIN_HITS, MAX_HITS, SUBJECTS } from '../../constants';

const optimizationRoute = 'http://localhost:8000/optimize';
const coursesRoute = 'http://localhost:8000/courses';
const foreignLanguagesRoute = 'http://localhost:8000/foreign-languages';
const entryModesRoute = 'http://localhost:8000/entry-modes';
const YEAR_OPTIONS = ['2022', '2023', '2024', '2025'];

// Mantendo o MOCK_DATA com os std_scores necessários para o payload atual
const MOCK_DATA = {
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
    
    // Estado do formulário - Inicializado vazio para os selects dinâmicos
    const [course, setCourse] = useState('');
    const [referenceYear, setReferenceYear] = useState('');
    const [language, setLanguage] = useState('');
    const [entryMethod, setEntryMethod] = useState('');
    
    // Estado para as opções dos selects e loading
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

    // Efeito para carregar Modalidades e Línguas Estrangeiras
    useEffect(() => {
      let isCancelled = false;

      const fetchSelectionOptions = async () => {
        setIsLoadingSelectionOptions(true);
        try {
          const [languagesResponse, entryModesResponse] = await Promise.all([
            fetch(foreignLanguagesRoute),
            fetch(entryModesRoute),
          ]);

          if (!languagesResponse.ok || !entryModesResponse.ok) {
            throw new Error('Falha ao carregar opções de formulário');
          }

          const [fetchedLanguages, fetchedEntryModes] = await Promise.all([
            languagesResponse.json(),
            entryModesResponse.json(),
          ]);

          if (!isCancelled) {
            setLanguageOptions(fetchedLanguages);
            setEntryMethodOptions(fetchedEntryModes);
          }
        } catch (error) {
          if (!isCancelled) {
            setLanguageOptions([]);
            setEntryMethodOptions([]);
            alert('Erro ao carregar opções de Língua Estrangeira e Forma de Acesso.');
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
            yearOptions={YEAR_OPTIONS}
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