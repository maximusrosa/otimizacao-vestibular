import '../../index.css';
import './styles.css';
import { Bar, BarChart, XAxis, YAxis, CartesianGrid, Tooltip, Legend, LabelList } from 'recharts';

const ResultsView = ({ 
    provasResultados, 
    resumoResultados, 
    rankingClassificacao,
    formatarNumero,
    navigate,
    historicalData 
}) => {
    return (
        <div className="container">
            <h1>Otimizador de Acertos - Vestibular UFRGS</h1>

            <p className="description">
                Esse resultado é o que possui o menor erro de Escore Padronizado (EP) das matérias selecionadas anteriormente que anda é mais alta a nota de corte, segundo o ano e
                forma de ingresso selecionado.
            </p>

            <hr />

            <div className="table-wrapper">
                <table className="results-table table-header-primary table-centered">
                    <thead>
                        <tr>
                            <th>Prova</th>
                            <th>Acertos</th>
                            <th>Escore Padronizado</th>
                            <th>Média</th>
                            <th>Desvio Padrão</th>
                        </tr>
                    </thead>
                    <tbody>
                        {provasResultados.map((prova, index) => (
                            <tr key={index}>
                                <td>{prova.prova}</td>
                                <td>{prova.acertos}</td>
                                <td>{formatarNumero(prova.escorePadronizado, 2)}</td>
                                <td>{formatarNumero(prova.media, 4)}</td>
                                <td>{formatarNumero(prova.desvioPadrao, 4)}</td>
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
                    <div className="card-description">Seria aprovado no Listão em 2026<br/>(&gt;= nota de corte)</div>
                </div>
                <div className="card card-info">
                    <div className="card-title">Nota de corte do Listão 2026</div>
                    <div className="card-circle card-circle-purple">
                        <div className="card-circle-value">{formatarNumero(resumoResultados.mediaPonderada, 2)}</div>
                    </div>
                </div>
                <div className="card card-info">
                    <div className="card-title">Sua classificação</div>
                    <div className="card-subtitle-gray">(se fosse no Vestibular 2026)</div>
                    <div className="card-circle card-circle-gray">
                        <div className="card-classification">
                            <div>Geral: {resumoResultados.colocacao}º</div>
                            <div className="card-classification-cota">Cota L3/L5/L1_EP: —</div>
                        </div>
                    </div>
                </div>
            </div>

            <h2 className="ranking-section">Classificação - Inscrições UFRGS</h2>

            <div className="table-wrapper ranking-table-wrapper">
                <table className="ranking-table table-header-secondary table-centered">
                    <thead>
                        <tr>
                            <th>Classificação</th>
                            <th>Média</th>
                            <th>Vaga(s) de concorrência</th>
                            <th>Vaga de ingresso</th>
                            <th>Período vaga</th>
                            <th>Listão</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rankingClassificacao.map((candidato, index) => (
                            <tr key={index} className={candidato.simulado ? 'table-row-highlight' : ''}>
                                <td>{candidato.classificacao}</td>
                                <td>{candidato.media}</td>
                                <td>{candidato.vagasConcorrencia}</td>
                                <td>{candidato.vagaIngresso}</td>
                                <td>{candidato.periodoVaga}</td>
                                <td>{candidato.listao}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {historicalData && Object.keys(historicalData).length > 0 && (
                <div className="historical-data-graph">
                    <h2 className="ranking-section">Notas de Corte Históricas (Últimos 5 Anos)</h2>
                    <div style={{ display: 'flex', justifyContent: 'center', width: '100%' }}>
                        <BarChart 
                            width={700} 
                            height={400} 
                            data={Object.entries(historicalData)
                                .sort(([yearA], [yearB]) => parseInt(yearA) - parseInt(yearB))
                                .map(([year, score]) => ({ 
                                    year, 
                                    'Nota de Corte': parseFloat(score.toFixed(2))
                                }))}
                            margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                        >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis 
                                dataKey="year" 
                            />
                            <YAxis 
                                domain={[
                                    (dataMin) => Math.floor(dataMin * 0.98), 
                                    (dataMax) => Math.ceil(dataMax * 1.02)
                                ]}
                            />
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