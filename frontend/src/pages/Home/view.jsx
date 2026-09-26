import '../../index.css';
import './styles.css';
import Selector from '../../components/Selector';
import Checkbox from '../../components/Checkbox';
import { SUBJECTS } from '../../constants';

const HomeView = ({
    course, setCourse,
    referenceYear, setReferenceYear,
    language, setLanguage,
    entryMethod, setEntryMethod,
    handleOptimize,
    subjects, handleSubjectChange,
    yearOptions, courseOptions, languageOptions, entryMethodOptions,
    isCourseSelectionEnabled, hasReferenceYearSelected,
    isLoadingCourses, isLoadingSelectionOptions,
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
                <Selector
                    label="Ano"
                    value={referenceYear}
                    onChange={setReferenceYear}
                    options={yearOptions}
                    placeholder={isLoadingSelectionOptions ? 'Carregando opções...' : 'Selecione o ano'}
                    disabled={isLoadingSelectionOptions || yearOptions.length === 0}
                />

                <Selector
                    label="Selecione seu curso"
                    value={course}
                    onChange={setCourse}
                    options={courseOptions}
                    placeholder={
                        !hasReferenceYearSelected
                            ? 'Selecione o ano primeiro'
                            : isLoadingCourses
                              ? 'Carregando cursos...'
                              : 'Selecione o curso'
                    }
                    disabled={!isCourseSelectionEnabled}
                />

                <Selector
                    label="Língua Estrangeira"
                    value={language}
                    onChange={setLanguage}
                    options={languageOptions}
                    placeholder={isLoadingSelectionOptions ? 'Carregando opções...' : 'Selecione a língua'}
                    disabled={isLoadingSelectionOptions || languageOptions.length === 0}
                />

                <Selector
                    label="Forma de Acesso"
                    value={entryMethod}
                    onChange={setEntryMethod}
                    options={entryMethodOptions}
                    placeholder={isLoadingSelectionOptions ? 'Carregando opções...' : 'Selecione a forma de acesso'}
                    disabled={isLoadingSelectionOptions || entryMethodOptions.length === 0}
                />
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
                    {SUBJECTS.map(({ id, name }) => (
                        <tr key={id}>
                            <Checkbox
                                id={id}
                                label={name}
                                checked={subjects[id].minimize}
                                onChange={(e) => handleSubjectChange(id, 'minimize', e.target.checked)}
                            />
                            <td>
                                <input
                                    type="number"
                                    value={subjects[id].min}
                                    onChange={(e) => handleSubjectChange(id, 'min', e.target.value)}
                                />
                            </td>
                            <td>
                                <input
                                    type="number"
                                    value={subjects[id].max}
                                    onChange={(e) => handleSubjectChange(id, 'max', e.target.value)}
                                />
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <div className="actions">
                <button className="main-button" onClick={() => { handleOptimize(); }}>Otimizar</button>
            </div>
        </div>
    );
};

export default HomeView;
