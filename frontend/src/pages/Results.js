import '../App.css';
import './Results.css';
import { useNavigate } from 'react-router-dom';

function Resultados(){
    const navigate = useNavigate();
    
    // Dados temporários de teste - Resultados das Provas
    const provasResultados = [
        { prova: 'Biologia', acertos: 12, escorePadronizado: 545.32, media: 8.5432, desvioPadrao: 2.3456 },
        { prova: 'Física', acertos: 15, escorePadronizado: 678.90, media: 10.2345, desvioPadrao: 3.1234 },
        { prova: 'Geografia', acertos: 10, escorePadronizado: 512.45, media: 7.8901, desvioPadrao: 2.5678 },
        { prova: 'História', acertos: 14, escorePadronizado: 623.78, media: 9.6789, desvioPadrao: 2.8901 },
        { prova: 'Literatura', acertos: 11, escorePadronizado: 567.23, media: 8.9012, desvioPadrao: 2.4567 },
        { prova: 'Matemática', acertos: 18, escorePadronizado: 734.56, media: 11.5678, desvioPadrao: 3.4567 },
        { prova: 'Português / Redação', acertos: 16, escorePadronizado: 689.34, media: 10.6789, desvioPadrao: 3.2345 },
        { prova: 'Língua Estrangeira', acertos: 13, escorePadronizado: 598.12, media: 9.1234, desvioPadrao: 2.6789 }
    ];

    // Dados temporários de teste - Cards de Resumo
    const resumoResultados = {
        notaTotal: 635.84,
        mediaPonderada: 624.72,
        colocacao: 64,
        vagas: '10/5/30',
        posicaoCota: 14
    };

    // Dados temporários de teste - Ranking/Classificação
    const rankingClassificacao = [
        {
            classificacao: '10º',
            media: '625,34',
            vagasConcorrencia: 'AC',
            vagaIngresso: 'Ampla Concorrência',
            periodoVaga: '2024/2',
            listao: 'Sim',
            simulado: false
        },
        {
            classificacao: '-',
            media: '622,84',
            vagasConcorrencia: '-',
            vagaIngresso: 'Ampla Concorrência',
            periodoVaga: '-',
            listao: '-',
            simulado: true
        },
        {
            classificacao: '11º',
            media: '620,12',
            vagasConcorrencia: 'AC',
            vagaIngresso: 'Ampla Concorrência',
            periodoVaga: '2024/2',
            listao: 'Sim',
            simulado: false
        },
        {
            classificacao: '12º',
            media: '618,45',
            vagasConcorrencia: 'AC',
            vagaIngresso: 'Ampla Concorrência',
            periodoVaga: '2024/2',
            listao: 'Não',
            simulado: false
        },
        {
            classificacao: '13º',
            media: '615,78',
            vagasConcorrencia: 'L2 - EP',
            vagaIngresso: 'Escola Pública',
            periodoVaga: '2024/2',
            listao: 'Não',
            simulado: false
        }
    ];

    // Função auxiliar para formatar números
    const formatarNumero = (numero, casasDecimais = 2) => {
        return numero.toFixed(casasDecimais).replace('.', ',');
    };

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

        <div className="actions">
            <button className="main-button" onClick={() => navigate('/')}>Voltar</button>
        </div>
        </div>
    );
}
export default Resultados;