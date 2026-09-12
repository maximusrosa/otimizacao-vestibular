import '../../index.css';
import './styles.css';

// Recebe tudo o que precisa via "props"
const HomeView = ({ 
    course, 
    setCourse, 
    referenceYear,
    setReferenceYear,
    language,
    setLanguage,
    entryMethod,
    setEntryMethod,
    essayScore,
    setEssayScore,
    handleOptimize, 
    subjects, 
    handleSubjectChange, 
}) => {
    return (
        <div className="container">
            <h1>Otimizador de Acertos - Vestibular UFRGS</h1>

            <p className="description">
                Digite seus acertos (1–15) e a nota da Redação (1–15 – cada campo mostra "/15" ao lado).
                Escolha o curso, idioma e a forma de acesso. O simulador calcula o escore padronizado
                e a média harmônica ponderada por curso, exibe a nota de corte (com seletor de ano)
                e a sua posição geral/cota, incluindo a linha "Nota Simulada" e frases de fila de espera
                quando cabíveis.
            </p>

            <div className="filters">
                <div className="field">
                    <label>Selecione seu curso</label>
                    <div className="select-wrapper">
                        <select value={course} onChange={setCourse}></select>
                        <button className="clear">×</button>
                    </div>
                </div>

                <div className="field">
                    <label>Ano</label>
                    <div className="select-wrapper">
                        <select value={referenceYear} onChange={setReferenceYear}></select>
                        <button className="clear">×</button>
                    </div>
                </div>

                <div className="field">
                    <label>Língua Estrangeira</label>
                    <div className="select-wrapper">
                        <select value={language} onChange={setLanguage}></select>
                        <button className="clear">×</button>
                    </div>
                </div>

                <div className="field">
                    <label>Forma de Acesso</label>
                    <div className="select-wrapper">
                        <select value={entryMethod} onChange={setEntryMethod}></select>
                        <button className="clear">×</button>
                    </div>
                </div>
                
                {/* NOVO CAMPO: Nota da Redação */}
                <div className="field">
                    <label>Nota da Redação</label>
                    <div className="select-wrapper">
                        <input 
                            type="number" 
                            step="0.01"
                            placeholder="Ex: 12.5"
                            value={essayScore} 
                            onChange={setEssayScore}
                            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
                        />
                    </div>
                </div>
            </div>

            <hr />

            <table>
                {/* ... (Todo o conteúdo da <thead> e <tbody> continua idêntico) ... */}
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
                        <td><input type="checkbox" id="BIO" checked={subjects.BIO.minimize} onChange={(e) => handleSubjectChange('BIO', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="BIO">Biologia</label></td>
                        <td><input type="number" value={subjects.BIO.min} onChange={(e) => handleSubjectChange('BIO', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.BIO.max} onChange={(e) => handleSubjectChange('BIO', 'max', e.target.value)} /></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="FIS" checked={subjects.FIS.minimize} onChange={(e) => handleSubjectChange('FIS', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="FIS">Física</label></td>
                        <td><input type="number" value={subjects.FIS.min} onChange={(e) => handleSubjectChange('FIS', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.FIS.max} onChange={(e) => handleSubjectChange('FIS', 'max', e.target.value)} /></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="QUI" checked={subjects.QUI.minimize} onChange={(e) => handleSubjectChange('QUI', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="QUI">Química</label></td>
                        <td><input type="number" value={subjects.QUI.min} onChange={(e) => handleSubjectChange('QUI', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.QUI.max} onChange={(e) => handleSubjectChange('QUI', 'max', e.target.value)} /></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="GEO" checked={subjects.GEO.minimize} onChange={(e) => handleSubjectChange('GEO', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="GEO">Geografia</label></td>
                        <td><input type="number" value={subjects.GEO.min} onChange={(e) => handleSubjectChange('GEO', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.GEO.max} onChange={(e) => handleSubjectChange('GEO', 'max', e.target.value)} /></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="HIS" checked={subjects.HIS.minimize} onChange={(e) => handleSubjectChange('HIS', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="HIS">História</label></td>
                        <td><input type="number" value={subjects.HIS.min} onChange={(e) => handleSubjectChange('HIS', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.HIS.max} onChange={(e) => handleSubjectChange('HIS', 'max', e.target.value)} /></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="LIT" checked={subjects.LIT.minimize} onChange={(e) => handleSubjectChange('LIT', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="LIT">Literatura</label></td>
                        <td><input type="number" value={subjects.LIT.min} onChange={(e) => handleSubjectChange('LIT', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.LIT.max} onChange={(e) => handleSubjectChange('LIT', 'max', e.target.value)} /></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="MAT" checked={subjects.MAT.minimize} onChange={(e) => handleSubjectChange('MAT', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="MAT">Matemática</label></td>
                        <td><input type="number" value={subjects.MAT.min} onChange={(e) => handleSubjectChange('MAT', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.MAT.max} onChange={(e) => handleSubjectChange('MAT', 'max', e.target.value)} /></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="PORT_RED" checked={subjects.PORT_RED.minimize} onChange={(e) => handleSubjectChange('PORT_RED', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="PORT_RED">Português / Redação</label></td>
                        <td><input type="number" value={subjects.PORT_RED.min} onChange={(e) => handleSubjectChange('PORT_RED', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.PORT_RED.max} onChange={(e) => handleSubjectChange('PORT_RED', 'max', e.target.value)} /></td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="LEM" checked={subjects.LEM.minimize} onChange={(e) => handleSubjectChange('LEM', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="LEM">Língua Estrangeira</label></td>
                        <td><input type="number" value={subjects.LEM.min} onChange={(e) => handleSubjectChange('LEM', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.LEM.max} onChange={(e) => handleSubjectChange('LEM', 'max', e.target.value)} /></td>
                    </tr>
                </tbody>
            </table>

            <div className="actions">
                <button className="main-button" onClick={() => {handleOptimize()}}>Otimizar</button>
            </div>
        </div>
    );
};

export default HomeView;