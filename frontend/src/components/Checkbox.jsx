const Checkbox = ({ id, label, checked, onChange }) => (
    <>
        <td><input type="checkbox" id={id} checked={checked} onChange={onChange} /></td>
        <td><label htmlFor={id}>{label}</label></td>
    </>
);

export default Checkbox;