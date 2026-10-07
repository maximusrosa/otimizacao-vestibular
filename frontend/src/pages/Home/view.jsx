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
  essayConstraints, handleEssayConstraintChange,
  portugueseMinimize, setPortugueseMinimize,
  essayMinimize, setEssayMinimize,
  handleOptimize,
  subjects, handleSubjectChange,
  yearOptions, courseOptions, languageOptions, entryMethodOptions,
  isCourseSelectionEnabled, hasReferenceYearSelected,
  isLoadingCourses, isLoadingSelectionOptions,
}) => {
  const renderObjectiveSubject = ({ id, name }) => (
    <tr key={id}>
      <Checkbox
        id={id}
        label={name}
        checked={subjects[id].minimize}
        onChange={(event) => handleSubjectChange(id, 'minimize', event.target.checked)}
      />
      <td>
        <input
          aria-label={`Acertos mínimos de ${name}`}
          type="number"
          min="1"
          max="15"
          value={subjects[id].min}
          onChange={(event) => handleSubjectChange(id, 'min', event.target.value)}
        />
      </td>
      <td>
        <input
          aria-label={`Acertos máximos de ${name}`}
          type="number"
          min="1"
          max="15"
          value={subjects[id].max}
          onChange={(event) => handleSubjectChange(id, 'max', event.target.value)}
        />
      </td>
    </tr>
  );

  const regularSubjects = SUBJECTS.filter(({ id }) => id !== 'PORT_RED' && id !== 'LEM');
  const foreignLanguageSubject = SUBJECTS.find(({ id }) => id === 'LEM');

  return (
    <div className="container">
      <h1>Otimizador de Acertos - Vestibular UFRGS</h1>

      <p className="description">
        Simulação com dados históricos. Defina os limites das provas e selecione quais componentes devem ser minimizados.
      </p>

      <div className="filters">
        <Selector
          id="reference-year"
          label="Ano"
          value={referenceYear}
          onChange={setReferenceYear}
          options={yearOptions}
          placeholder={isLoadingSelectionOptions ? 'Carregando opções...' : 'Selecione o ano'}
          disabled={isLoadingSelectionOptions || yearOptions.length === 0}
        />
        <Selector
          id="course"
          label="Selecione seu curso"
          value={course}
          onChange={setCourse}
          options={courseOptions}
          placeholder={!hasReferenceYearSelected
            ? 'Selecione o ano primeiro'
            : isLoadingCourses ? 'Carregando cursos...' : 'Selecione o curso'}
          disabled={!isCourseSelectionEnabled}
        />
        <Selector
          id="foreign-language"
          label="Língua Estrangeira"
          value={language}
          onChange={setLanguage}
          options={languageOptions}
          placeholder={isLoadingSelectionOptions ? 'Carregando opções...' : 'Selecione a língua'}
          disabled={isLoadingSelectionOptions || languageOptions.length === 0}
        />
        <Selector
          id="entry-method"
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
          {regularSubjects.map(renderObjectiveSubject)}
          <tr>
            <Checkbox
              id="PORT_RED"
              label="Português"
              checked={portugueseMinimize}
              onChange={(event) => setPortugueseMinimize(event.target.checked)}
            />
            <td>
              <input
                aria-label="Acertos mínimos de Português"
                type="number"
                min="1"
                max="15"
                value={subjects.PORT_RED.min}
                onChange={(event) => handleSubjectChange('PORT_RED', 'min', event.target.value)}
              />
            </td>
            <td>
              <input
                aria-label="Acertos máximos de Português"
                type="number"
                min="1"
                max="15"
                value={subjects.PORT_RED.max}
                onChange={(event) => handleSubjectChange('PORT_RED', 'max', event.target.value)}
              />
            </td>
          </tr>
          <tr>
            <Checkbox
              id="essay-objective"
              label="Redação"
              checked={essayMinimize}
              onChange={(event) => setEssayMinimize(event.target.checked)}
            />
            <td>
              <input
                aria-label="Nota mínima da Redação"
                type="number"
                min="4.5"
                max="15"
                step="0.1"
                value={essayConstraints.min}
                onChange={(event) => handleEssayConstraintChange('min', event.target.value)}
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
                onChange={(event) => handleEssayConstraintChange('max', event.target.value)}
              />
            </td>
          </tr>
          {renderObjectiveSubject(foreignLanguageSubject)}
        </tbody>
      </table>

      <p className="port-red-note">
        Ao marcar Português e Redação, a otimização considera a nota conjunta, composta em partes iguais.
      </p>

      <div className="actions">
        <button className="main-button" onClick={handleOptimize}>Otimizar</button>
      </div>
    </div>
  );
};

export default HomeView;
