// src/components/SelectField.tsx
// переиспользуемые компоненты select
import { h } from 'preact';

interface SelectFieldProps {
  name: string;
  label: string;
  value: string;
  options: Array<{ id: number; name: string }>;
  onChange: (name: string, value: string) => void;
  required?: boolean;
  placeholder?: string;
}

export const SelectField = ({
  name, label, value, options, onChange,
  required = false, placeholder = `Select ${label.toLowerCase()}`
}: SelectFieldProps) => {
  const getDisplayName = (item: any) => {
    return item.name || item.name_en || item.name_ru || item.name_fr ||
           item.name_es || item.name_it || item.name_de || item.name_zh || '';
  };

  return (
    <div>
      <label className="label">
        <span className="label-text">{label}{required && ' *'}</span>
      </label>
      <select
        name={name}
        value={value}
        onChange={(e: any) => onChange(name, e.target.value)}
        className="select select-bordered w-full"
        required={required}
      >
        <option value="">{placeholder}</option>
        {options.map(option => (
          <option key={option.id} value={option.id}>
            {getDisplayName(option)}
          </option>
        ))}
      </select>
    </div>
  );
};