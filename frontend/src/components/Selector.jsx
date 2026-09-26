const Selector = ({ label, value, onChange, options, placeholder, disabled }) => (
    <div className="field">
        <label>{label}</label>
        <div className="select-wrapper">
            <select value={value} onChange={onChange} disabled={disabled}>
                <option value="">{placeholder}</option>
                {options.map((option) => (
                    <option key={option} value={option}>
                        {option}
                    </option>
                ))}
            </select>
            <button className="clear" onClick={() => onChange({ target: { value: '' } })}>×</button>
        </div>
    </div>
);

export default Selector;