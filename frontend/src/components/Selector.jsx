const Selector = ({ id, label, value, onChange, options, placeholder, disabled }) => (
    <div className="field">
        <label htmlFor={id}>{label}</label>
        <div className="select-wrapper">
            <select id={id} value={value} onChange={onChange} disabled={disabled}>
                <option value="">{placeholder}</option>
                {options.map((option) => (
                    <option key={option} value={option}>
                        {option}
                    </option>
                ))}
            </select>
            <button type="button" className="clear" aria-label={`Limpar ${label}`} onClick={() => onChange({ target: { value: '' } })}>x</button>
        </div>
    </div>
);

export default Selector;
