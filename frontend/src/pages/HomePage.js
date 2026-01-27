import '../App.css';

function HomePage(){
    return (
        <div class="container">
        <h1>Otimizador de Acertos - Vestibular UFRGS</h1>

        <p class="description">
        Digite seus acertos (0–15) e a nota da Redação (0–15 – cada campo mostra “/15” ao lado).
        Escolha o curso, idioma e a forma de acesso. O simulador calcula o escore padronizado
        e a média harmônica ponderada por curso, exibe a nota de corte (com seletor de ano)
        e a sua posição geral/cota, incluindo a linha “Nota Simulada” e frases de fila de espera
        quando cabíveis.
        </p>

        <div class="filters">
        <div class="field">
            <label>Selecione seu curso</label>
            <div class="select-wrapper">
            <select></select>
            <button class="clear">×</button>
            </div>
        </div>

        <div class="field">
            <label>Ano</label>
            <div class="select-wrapper">
            <select></select>
            <button class="clear">×</button>
            </div>
        </div>

        <div class="field">
            <label>Língua Estrangeira</label>
            <div class="select-wrapper">
            <select></select>
            <button class="clear">×</button>
            </div>
        </div>

        <div class="field">
            <label>Forma de Acesso</label>
            <div class="select-wrapper">
            <select></select>
            <button class="clear">×</button>
            </div>
        </div>
        </div>

        <hr />

        <table>
        <thead>
            <tr>
            <th>Minimizar</th>
            <th>Prova</th>
            <th colspan="2">Acertos</th>
            </tr>
            <tr class="subhead">
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

        <div class="actions">
        <button class="main-button">Otimizar</button>
        </div>
    </div>
    );
}
export default HomePage;

