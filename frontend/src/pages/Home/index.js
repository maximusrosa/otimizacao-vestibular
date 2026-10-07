import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import HomeView from './view';
import { MIN_HITS, MAX_HITS, SUBJECTS } from '../../constants';

const apiUrl = 'http://localhost:8000';

function HomePage() {
  const navigate = useNavigate();

  const [course, setCourse] = useState('');
  const [referenceYear, setReferenceYear] = useState('');
  const [language, setLanguage] = useState('');
  const [entryMethod, setEntryMethod] = useState('');

  const [yearOptions, setYearOptions] = useState([]);
  const [courseOptions, setCourseOptions] = useState([]);
  const [languageOptions, setLanguageOptions] = useState([]);
  const [entryMethodOptions, setEntryMethodOptions] = useState([]);
  const [isLoadingCourses, setIsLoadingCourses] = useState(false);
  const [isLoadingSelectionOptions, setIsLoadingSelectionOptions] = useState(false);

  const [essayConstraints, setEssayConstraints] = useState({ min: 4.5, max: 15 });
  const [portugueseMinimize, setPortugueseMinimize] = useState(false);
  const [essayMinimize, setEssayMinimize] = useState(false);
  const [subjectsData, setSubjectsData] = useState(
    SUBJECTS.reduce((subjects, subject) => ({
      ...subjects,
      [subject.id]: { min: MIN_HITS, max: MAX_HITS, minimize: false },
    }), {})
  );

  useEffect(() => {
    let cancelled = false;

    async function fetchSelectionOptions() {
      setIsLoadingSelectionOptions(true);
      try {
        const responses = await Promise.all([
          fetch(`${apiUrl}/years`),
          fetch(`${apiUrl}/foreign-languages`),
          fetch(`${apiUrl}/entry-modes`),
        ]);
        if (responses.some((response) => !response.ok)) {
          throw new Error('Falha ao carregar opções do formulário.');
        }

        const [years, languages, entryModes] = await Promise.all(
          responses.map((response) => response.json())
        );
        if (!cancelled) {
          setYearOptions(years);
          setLanguageOptions(languages);
          setEntryMethodOptions(entryModes);
        }
      } catch (error) {
        if (!cancelled) {
          alert('Erro ao carregar anos, línguas estrangeiras e formas de acesso.');
          console.error(error);
        }
      } finally {
        if (!cancelled) setIsLoadingSelectionOptions(false);
      }
    }

    fetchSelectionOptions();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    if (!referenceYear) {
      setCourseOptions([]);
      return undefined;
    }

    let cancelled = false;
    async function fetchCourses() {
      setIsLoadingCourses(true);
      try {
        const response = await fetch(`${apiUrl}/courses?reference_year=${referenceYear}`);
        if (!response.ok) throw new Error(`Falha ao buscar cursos: ${response.status}`);
        const courses = await response.json();
        if (!cancelled) setCourseOptions(courses);
      } catch (error) {
        if (!cancelled) {
          setCourseOptions([]);
          alert('Erro ao carregar cursos. Verifique se o backend está rodando.');
          console.error(error);
        }
      } finally {
        if (!cancelled) setIsLoadingCourses(false);
      }
    }

    fetchCourses();
    return () => { cancelled = true; };
  }, [referenceYear]);

  const handleSubjectChange = (id, field, value) => {
    if (field === 'min' || field === 'max') {
      if (value === '') {
        setSubjectsData((previous) => ({ ...previous, [id]: { ...previous[id], [field]: value } }));
        return;
      }
      const integer = Number.parseInt(value, 10);
      if (!Number.isInteger(integer) || integer < MIN_HITS || integer > MAX_HITS) return;
    }
    setSubjectsData((previous) => ({ ...previous, [id]: { ...previous[id], [field]: value } }));
  };

  const handleReferenceYearChange = (event) => {
    setReferenceYear(event.target.value);
    setCourse('');
  };

  const portRedObjective = portugueseMinimize
    ? (essayMinimize ? 'combined' : 'portuguese')
    : (essayMinimize ? 'essay' : 'none');

  const handleOptimize = async () => {
    if (!referenceYear || !course || !language || !entryMethod) {
      alert('Selecione ano, curso, língua estrangeira e forma de acesso antes de otimizar.');
      return;
    }

    const essayMin = Number.parseFloat(essayConstraints.min);
    const essayMax = Number.parseFloat(essayConstraints.max);
    const invalidPrecision = [essayMin, essayMax]
      .some((value) => Math.abs(value * 10 - Math.round(value * 10)) > 1e-9);
    if ([essayMin, essayMax].some(Number.isNaN)
      || essayMin < 4.5 || essayMax > 15 || essayMin > essayMax || invalidPrecision) {
      alert('Informe limites de Redação entre 4,5 e 15 usando uma casa decimal.');
      return;
    }

    const minSubjects = Object.entries(subjectsData)
      .filter(([id, data]) => id !== 'PORT_RED' && data.minimize)
      .map(([id]) => id);

    const constraints = {};
    Object.entries(subjectsData).forEach(([id, data]) => {
      const subjectConstraints = [];
      if (data.min !== '') subjectConstraints.push(['>=', Number.parseInt(data.min, 10)]);
      if (data.max !== '') subjectConstraints.push(['<=', Number.parseInt(data.max, 10)]);
      if (subjectConstraints.length) constraints[id] = subjectConstraints;
    });

    const payload = {
      course,
      constraints,
      min_subjects: minSubjects,
      foreign_language: language,
      reference_year: referenceYear,
      entry_method: entryMethod,
      essay_constraints: { min: essayMin, max: essayMax },
      port_red_objective: portRedObjective,
    };

    try {
      const response = await fetch(`${apiUrl}/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) {
        console.error('Erro do servidor:', result);
        alert('Erro na otimização. Verifique os dados enviados.');
        return;
      }
      navigate('/resultados', {
        state: {
          results: result.result,
          historicalData: result.graphJson,
          simulation: { course, referenceYear, entryMethod },
        },
      });
    } catch (error) {
      alert('Erro na requisição. Verifique se o backend está rodando.');
      console.error(error);
    }
  };

  return (
    <HomeView
      course={course}
      setCourse={(event) => setCourse(event.target.value)}
      referenceYear={referenceYear}
      setReferenceYear={handleReferenceYearChange}
      language={language}
      setLanguage={(event) => setLanguage(event.target.value)}
      entryMethod={entryMethod}
      setEntryMethod={(event) => setEntryMethod(event.target.value)}
      essayConstraints={essayConstraints}
      handleEssayConstraintChange={(field, value) => setEssayConstraints((previous) => ({ ...previous, [field]: value }))}
      portugueseMinimize={portugueseMinimize}
      setPortugueseMinimize={setPortugueseMinimize}
      essayMinimize={essayMinimize}
      setEssayMinimize={setEssayMinimize}
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
