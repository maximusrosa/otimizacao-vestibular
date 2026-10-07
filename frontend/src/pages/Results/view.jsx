import '../../index.css';
import './styles.css';
import { Bar, BarChart, XAxis, YAxis, CartesianGrid, Legend, LabelList } from 'recharts';

const ResultsView = ({
  provasResultados,
  resumoResultados,
  rankingClassificacao,
  ranking,
  rankingError,
  isLoadingRanking,
  entryModeFilter,
  entryModeOptions,
  handleFilterChange,
  goToPreviousPage,
  goToNextPage,
  returnToSimulation,
  formatarNumero,
  navigate,
  historicalData,
  referenceYear,
}) => {
  const firstPosition = ranking.total ? ranking.offset + 1 : 0;
  const lastPosition = Math.min(ranking.offset + ranking.limit, ranking.total);
  const updatedAt = ranking.last_synced_at
    ? new Date(ranking.last_synced_at).toLocaleString('pt-BR')
    : null;

  return (
    <div className="container results-container">
      <h1>Otimizador de Acertos - Vestibular UFRGS</h1>
      <p className="description">
        Combinação otimizada com os dados históricos e a nota de corte do vestibular selecionado.
      </p>

      <hr />

      <div className="table-wrapper">
        <table className="results-table table-header-primary table-centered">
          <thead>
            <tr>
              <th>Prova</th>
              <th>Acertos / Nota</th>
              <th>Escore Padronizado</th>
            </tr>
          </thead>
          <tbody>
            {provasResultados.map((prova) => (
              <tr key={prova.prova}>
                <td>{prova.prova}</td>
                <td>{prova.resultado}</td>
                <td>{formatarNumero(prova.escorePadronizado, 2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="cards-grid">
        <div className="card card-info">
          <div className="card-title">Sua nota final</div>
          <div className="card-circle card-circle-green">
            <div className="card-circle-value">{formatarNumero(resumoResultados.notaTotal, 2)}</div>
          </div>
          <div className="card-description">
            {resumoResultados.aprovado ? 'Atinge' : 'Não atinge'} a nota de corte de {referenceYear || 'referência'}
          </div>
        </div>
        <div className="card card-info">
          <div className="card-title">Nota de corte</div>
          <div className="card-circle card-circle-purple">
            <div className="card-circle-value">{formatarNumero(resumoResultados.notaCorte, 2)}</div>
          </div>
        </div>
        <div className="card card-info">
          <div className="card-title">Posição estimada</div>
          <div className="card-circle card-circle-gray">
            <div className="card-classification">
              {resumoResultados.colocacao ? `${resumoResultados.colocacao}º` : '—'}
            </div>
          </div>
          <div className="card-subtitle-gray">Empates são posicionados antes da simulação</div>
        </div>
      </div>

      <section className="ranking-section" aria-labelledby="ranking-title">
        <div className="ranking-heading">
          <div>
            <h2 id="ranking-title">Classificação de candidatos</h2>
            <p className="ranking-freshness">
              {updatedAt ? `Atualizado em ${updatedAt}` : 'Ainda não há sincronização detalhada para esta seleção.'}
              {ranking.is_stale && updatedAt ? ' Dados possivelmente desatualizados.' : ''}
            </p>
          </div>
          <div className="ranking-filter field">
            <label htmlFor="ranking-entry-mode">Modalidade</label>
            <select id="ranking-entry-mode" value={entryModeFilter} onChange={handleFilterChange}>
              <option value="">Curso inteiro</option>
              {entryModeOptions.map((mode) => <option key={mode} value={mode}>{mode}</option>)}
            </select>
          </div>
        </div>

        {rankingError && <p className="ranking-message ranking-error">{rankingError}</p>}
        {isLoadingRanking && <p className="ranking-message">Carregando classificação...</p>}

        {!isLoadingRanking && !rankingError && (
          <>
            <div className="table-wrapper ranking-table-wrapper">
              <table className="ranking-table table-header-secondary table-centered">
                <thead>
                  <tr>
                    <th>Posição</th>
                    <th>Classificação UFRGS</th>
                    <th>Nome</th>
                    <th>Média</th>
                    <th>Vaga remanejada</th>
                    <th>Vaga(s) de concorrência</th>
                    <th>Vaga de ingresso</th>
                    <th>Situação</th>
                    <th>Data da situação</th>
                  </tr>
                </thead>
                <tbody>
                  {rankingClassificacao.map((candidate) => (
                    <tr
                      key={candidate.simulated ? 'simulation' : `${candidate.position}-${candidate.name}`}
                      className={candidate.simulated ? 'table-row-highlight' : ''}
                    >
                      <td>{candidate.position ? `${candidate.position}º` : '—'}</td>
                      <td>{candidate.source_classification ?? '—'}</td>
                      <td>{candidate.name || '—'}</td>
                      <td>{formatarNumero(candidate.final_score, 2)}</td>
                      <td>{candidate.remapped_vacancy || '—'}</td>
                      <td>{candidate.competition_vacancies || '—'}</td>
                      <td>{candidate.entry_vacancy || '—'}</td>
                      <td>{candidate.status || '—'}</td>
                      <td>{candidate.status_date ? new Date(`${candidate.status_date}T00:00:00`).toLocaleDateString('pt-BR') : '—'}</td>
                    </tr>
                  ))}
                  {!rankingClassificacao.length && (
                    <tr><td colSpan="9">Nenhum candidato detalhado encontrado.</td></tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="ranking-pagination">
              <button type="button" onClick={goToPreviousPage} disabled={ranking.offset === 0}>Anterior</button>
              <span>{firstPosition}–{lastPosition} de {ranking.total}</span>
              <button type="button" onClick={goToNextPage} disabled={lastPosition >= ranking.total}>Próxima</button>
              <button type="button" onClick={returnToSimulation} disabled={!ranking.simulated_position}>Ir para minha nota</button>
            </div>
          </>
        )}

        <p className="ranking-source">
          Fonte: dados públicos de chamamento da UFRGS. A posição simulada não aplica critérios de desempate individuais.
        </p>
      </section>

      {historicalData && Object.keys(historicalData).length > 0 && (
        <div className="historical-data-graph">
          <h2>Notas de corte históricas desde 2022</h2>
          <div className="chart-wrapper">
            <BarChart
              width={700}
              height={400}
              data={Object.entries(historicalData)
                .sort(([yearA], [yearB]) => parseInt(yearA, 10) - parseInt(yearB, 10))
                .map(([year, score]) => ({ year, 'Nota de Corte': Number(score.toFixed(2)) }))}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis domain={[(dataMin) => Math.floor(dataMin * 0.98), (dataMax) => Math.ceil(dataMax * 1.02)]} />
              <Legend />
              <Bar dataKey="Nota de Corte" fill="#0b5fa5">
                <LabelList dataKey="Nota de Corte" position="top" formatter={(value) => value.toFixed(2)} />
              </Bar>
            </BarChart>
          </div>
        </div>
      )}

      <div className="actions">
        <button className="main-button" onClick={() => navigate('/')}>Voltar</button>
      </div>
    </div>
  );
};

export default ResultsView;
