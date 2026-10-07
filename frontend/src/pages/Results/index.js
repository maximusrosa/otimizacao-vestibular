import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import ResultsView from './view';

const apiUrl = 'http://localhost:8000';
const PAGE_SIZE = 25;

function Resultados() {
  const navigate = useNavigate();
  const location = useLocation();
  const { results, historicalData, simulation } = location.state || {};
  const simulationCourse = simulation?.course;
  const simulationYear = simulation?.referenceYear;

  const [entryModeFilter, setEntryModeFilter] = useState(simulation?.entryMethod || '');
  const [entryModeOptions, setEntryModeOptions] = useState([]);
  const [requestedOffset, setRequestedOffset] = useState(null);
  const [ranking, setRanking] = useState({
    items: [], total: 0, offset: 0, limit: PAGE_SIZE,
    simulated_position: null, last_synced_at: null, is_stale: true,
  });
  const [isLoadingRanking, setIsLoadingRanking] = useState(false);
  const [rankingError, setRankingError] = useState('');
  const [rankingRequestVersion, setRankingRequestVersion] = useState(0);

  useEffect(() => {
    fetch(`${apiUrl}/entry-modes`)
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Falha ao carregar modalidades.')))
      .then(setEntryModeOptions)
      .catch(() => setEntryModeOptions([]));
  }, []);

  useEffect(() => {
    if (!simulationCourse || !simulationYear || results?.AC === undefined) return undefined;
    let cancelled = false;

    async function loadRanking() {
      setIsLoadingRanking(true);
      setRankingError('');
      const params = new URLSearchParams({
        year: simulationYear,
        course: simulationCourse,
        anchor_score: String(results.AC),
        limit: String(PAGE_SIZE),
      });
      if (entryModeFilter) params.set('entry_mode', entryModeFilter);
      if (requestedOffset !== null) params.set('offset', String(requestedOffset));

      try {
        const response = await fetch(`${apiUrl}/rankings/candidates?${params.toString()}`);
        if (!response.ok) throw new Error(`Falha ao carregar ranking: ${response.status}`);
        const data = await response.json();
        if (!cancelled) setRanking(data);
      } catch (error) {
        if (!cancelled) {
          setRankingError('O ranking detalhado não está disponível no momento.');
          console.error(error);
        }
      } finally {
        if (!cancelled) setIsLoadingRanking(false);
      }
    }

    loadRanking();
    return () => { cancelled = true; };
  }, [entryModeFilter, requestedOffset, rankingRequestVersion, results?.AC, simulationCourse, simulationYear]);

  const handleFilterChange = (event) => {
    setEntryModeFilter(event.target.value);
    setRequestedOffset(null);
  };

  const goToPreviousPage = () => setRequestedOffset(Math.max(0, ranking.offset - PAGE_SIZE));
  const goToNextPage = () => setRequestedOffset(ranking.offset + PAGE_SIZE);
  const returnToSimulation = useCallback(() => {
    setRequestedOffset(null);
    setRankingRequestVersion((version) => version + 1);
  }, []);

  const subjectNames = {
    BIO: 'Biologia', FIS: 'Física', GEO: 'Geografia', HIS: 'História',
    LIT: 'Literatura', MAT: 'Matemática', LEM: 'Língua Estrangeira', QUI: 'Química',
  };
  const chosenHits = results?.chosen_hits || {};
  const provasResultados = Object.entries(chosenHits)
    .filter(([subject]) => subject !== 'PORT_RED')
    .map(([subject, data]) => ({
      prova: subjectNames[subject] || subject,
      resultado: data.num_hits,
      escorePadronizado: data.EP,
    }));

  if (chosenHits.PORT_RED) {
    provasResultados.push(
      {
        prova: 'Português',
        resultado: chosenHits.PORT_RED.num_hits,
        escorePadronizado: chosenHits.PORT_RED.portuguese_EP,
      },
      {
        prova: 'Redação',
        resultado: chosenHits.PORT_RED.essay_score.toFixed(1),
        escorePadronizado: chosenHits.PORT_RED.essay_EP,
      },
      {
        prova: 'Português e Redação (50/50)',
        resultado: '—',
        escorePadronizado: chosenHits.PORT_RED.EP,
      }
    );
  }

  const rankingRows = useMemo(() => {
    const rows = ranking.items.map((candidate) => ({ ...candidate, simulated: false }));
    if (!ranking.simulated_position) return rows;

    const insertionIndex = ranking.simulated_position - 1 - ranking.offset;
    if (insertionIndex >= 0 && insertionIndex <= rows.length) {
      rows.splice(insertionIndex, 0, {
        position: ranking.simulated_position,
        source_classification: null,
        name: 'Sua simulação',
        final_score: results?.AC || 0,
        remapped_vacancy: null,
        competition_vacancies: entryModeFilter || 'Todas',
        entry_vacancy: entryModeFilter || 'Todas',
        status: 'Posição estimada',
        status_date: null,
        simulated: true,
      });
    }
    return rows;
  }, [entryModeFilter, ranking, results?.AC]);

  const resumoResultados = {
    notaTotal: results?.AC || 0,
    notaCorte: results?.threshold || 0,
    colocacao: ranking.simulated_position,
    aprovado: Boolean(results && results.AC >= results.threshold),
  };

  const formatarNumero = (numero, casasDecimais = 2) => {
    if (numero === null || numero === undefined) return '—';
    return Number(numero).toFixed(casasDecimais).replace('.', ',');
  };

  return (
    <ResultsView
      provasResultados={provasResultados}
      resumoResultados={resumoResultados}
      rankingClassificacao={rankingRows}
      ranking={ranking}
      rankingError={rankingError}
      isLoadingRanking={isLoadingRanking}
      entryModeFilter={entryModeFilter}
      entryModeOptions={entryModeOptions}
      handleFilterChange={handleFilterChange}
      goToPreviousPage={goToPreviousPage}
      goToNextPage={goToNextPage}
      returnToSimulation={returnToSimulation}
      formatarNumero={formatarNumero}
      navigate={navigate}
      historicalData={historicalData}
      referenceYear={simulationYear}
    />
  );
}

export default Resultados;
