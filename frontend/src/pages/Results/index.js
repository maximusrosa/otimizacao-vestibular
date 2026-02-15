import { useNavigate, useLocation } from 'react-router-dom';
import ResultsView from './view';

function Resultados(){
    const navigate = useNavigate();
    const location = useLocation();
    
    // Extrai os dados enviados pela página anterior
    const { results, historicalData } = location.state || {};
    
    console.log("Dados de otimização:", results);
    console.log("Dados históricos de notas de corte:", historicalData);
    
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
        <ResultsView 
            provasResultados={provasResultados}
            resumoResultados={resumoResultados}
            rankingClassificacao={rankingClassificacao}
            formatarNumero={formatarNumero}
            navigate={navigate}
            historicalData={historicalData}
        />
    );
}

export default Resultados;