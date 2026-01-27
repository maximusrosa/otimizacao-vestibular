import '../App.css';
import { useNavigate } from 'react-router-dom';

function HomePage(){
    const navigate = useNavigate();

    return (
    <div className="container">
    <h1>Otimizador de Acertos - Vestibular UFRGS</h1>

    <p className="description">
    Digite seus acertos (0–15) e a nota da Redação (0–15 – cada campo mostra “/15” ao lado).
    Escolha o curso, idioma e a forma de acesso. O simulador calcula o escore padronizado
    e a média harmônica ponderada por curso, exibe a nota de corte (com seletor de ano)
    e a sua posição geral/cota, incluindo a linha “Nota Simulada” e frases de fila de espera
    quando cabíveis.
    </p>

    <div className="filters">
    <div className="field">
        <label>Selecione seu curso</label>
        <div className="select-wrapper">
        <select></select>
        <button className="clear">×</button>
        </div>
    </div>

    <div className="field">
        <label>Ano</label>
        <div className="select-wrapper">
        <select></select>
        <button className="clear">×</button>
        </div>
    </div>

    <div className="field">
        <label>Língua Estrangeira</label>
        <div className="select-wrapper">
        <select></select>
        <button className="clear">×</button>
        </div>
    </div>

    <div className="field">
        <label>Forma de Acesso</label>
        <div className="select-wrapper">
        <select></select>
        <button className="clear">×</button>
        </div>
    </div>
    </div>

    <hr />

    <table>
    <thead>
        <tr>
        <th>Minimizar</th>
        <th>Prova</th>
        <th colSpan="2">Acertos</th>
        </tr>
        <tr className="subhead">
        <th></th>
        <th></th>
        <th>min</th>
        <th>max</th>
        </tr>
    </thead>
    <tbody>
        <tr>
        <td><input type="checkbox" /></td>
        <td>Biologia</td>
        <td><input type="number" /></td>
        <td><input type="number" /></td>
        </tr>
        <tr>
        <td><input type="checkbox" /></td>
        <td>Física</td>
        <td><input type="number" /></td>
        <td><input type="number" /></td>
        </tr>
        <tr>
        <td><input type="checkbox" /></td>
        <td>Geografia</td>
        <td><input type="number" /></td>
        <td><input type="number" /></td>
        </tr>
        <tr>
        <td><input type="checkbox" /></td>
        <td>História</td>
        <td><input type="number" /></td>
        <td><input type="number" /></td>
        </tr>
        <tr>
        <td><input type="checkbox" /></td>
        <td>Literatura</td>
        <td><input type="number" /></td>
        <td><input type="number" /></td>
        </tr>
        <tr>
        <td><input type="checkbox" /></td>
        <td>Matemática</td>
        <td><input type="number" /></td>
        <td><input type="number" /></td>
        </tr>
        <tr>
        <td><input type="checkbox" /></td>
        <td>Português / Redação</td>
        <td><input type="number" /></td>
        <td><input type="number" /></td>
        </tr>
        <tr>
        <td><input type="checkbox" /></td>
        <td>Língua Estrangeira</td>
        <td><input type="number" /></td>
        <td><input type="number" /></td>
        </tr>
    </tbody>
    </table>

    <div className="actions">
    <button className="main-button" onClick={() => navigate('/resultados')}>Otimizar</button>
    </div>
    </div>
    );
}
export default HomePage;


