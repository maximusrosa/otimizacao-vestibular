import { useNavigate, useLocation } from 'react-router-dom';
import ResultsView from './view';

function Resultados(){
    const navigate = useNavigate();
    const location = useLocation();
    
    // Extrai os dados enviados pela página anterior
    const { results, historicalData } = location.state || {};
    
    console.log("Dados de otimização:", results);
    console.log("Dados históricos de notas de corte:", historicalData);
    
    const subjectNames = {
        BIO: 'Biologia', FIS: 'Física', GEO: 'Geografia', HIS: 'História',
        LIT: 'Literatura', MAT: 'Matemática', LEM: 'Língua Estrangeira', QUI: 'Química'
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

    // Dados temporários de teste - Cards de Resumo
    const resumoResultados = {
        notaTotal: results?.AC || 0,
        mediaPonderada: results?.threshold || 0,
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
        if (numero === null || numero === undefined) return '—';
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
