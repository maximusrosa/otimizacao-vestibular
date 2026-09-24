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
    essayConstraints,
    handleEssayConstraintChange,
    portRedObjective,
    setPortRedObjective,
    handleOptimize, 
    subjects, 
    handleSubjectChange, 
}) => {
    return (
        <div className="container">
            <h1>Otimizador de Acertos - Vestibular UFRGS</h1>

            <p className="description">
                Defina os limites de acertos e da Redação, escolha o componente de Português e Redação
                que deve ser minimizado e execute a simulação para a nota de corte selecionada.
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
            </div>

            <hr />

            <table>
                {/* ... (Todo o conteúdo da <thead> e <tbody> continua idêntico) ... */}
                <thead>
                    <tr>
                        <th>Minimizar</th>
                        <th>Prova</th>
                        <th colSpan="2">Limites</th>
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
                        <td className="objective-managed">—</td>
                        <td><label htmlFor="PORT_RED">Português (acertos)</label></td>
                        <td><input type="number" value={subjects.PORT_RED.min} onChange={(e) => handleSubjectChange('PORT_RED', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.PORT_RED.max} onChange={(e) => handleSubjectChange('PORT_RED', 'max', e.target.value)} /></td>
                    </tr>
                    <tr>
                        <td className="objective-managed">—</td>
                        <td><label htmlFor="essay-min">Redação (nota)</label></td>
                        <td>
                            <input
                                id="essay-min"
                                aria-label="Nota mínima da Redação"
                                type="number"
                                min="4.5"
                                max="15"
                                step="0.1"
                                value={essayConstraints.min}
                                onChange={(e) => handleEssayConstraintChange('min', e.target.value)}
                            />
                        </td>
                        <td>
                            <input
                                aria-label="Nota máxima da Redação"
                                type="number"
                                min="4.5"
                                max="15"
                                step="0.1"
                                value={essayConstraints.max}
                                onChange={(e) => handleEssayConstraintChange('max', e.target.value)}
                            />
                        </td>
                    </tr>
                    <tr>
                        <td><input type="checkbox" id="LEM" checked={subjects.LEM.minimize} onChange={(e) => handleSubjectChange('LEM', 'minimize', e.target.checked)} /></td>
                        <td><label htmlFor="LEM">Língua Estrangeira</label></td>
                        <td><input type="number" value={subjects.LEM.min} onChange={(e) => handleSubjectChange('LEM', 'min', e.target.value)} /></td>
                        <td><input type="number" value={subjects.LEM.max} onChange={(e) => handleSubjectChange('LEM', 'max', e.target.value)} /></td>
                    </tr>
                </tbody>
            </table>

            <div className="port-red-objective field">
                <label htmlFor="port-red-objective">Objetivo de Português e Redação</label>
                <select id="port-red-objective" value={portRedObjective} onChange={setPortRedObjective}>
                    <option value="none">Não minimizar</option>
                    <option value="portuguese">Minimizar Português</option>
                    <option value="essay">Minimizar Redação</option>
                    <option value="combined">Minimizar nota conjunta</option>
                </select>
            </div>

            <div className="actions">
                <button className="main-button" onClick={() => {handleOptimize()}}>Otimizar</button>
            </div>
        </div>
    );
};

export default HomeView;
