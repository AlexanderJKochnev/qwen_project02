// src/components/SimpleField.tsx

import { h } from 'preact';

interface SimpleFieldProps {
  name: string;
  label: string;
  type?: 'text' | 'number' | 'email' | 'password';
  value: string | number;
  onChange: (name: string, value: string) => void;
  placeholder?: string;
  required?: boolean;
  step?: string;
  min?: number;
  max?: number;
  className?: string;
}

export const SimpleField = ({
  name,
  label,
  type = 'text',
  value,
  onChange,
  placeholder = '',
  required = false,
  step,
  min,
  max,
  className = ''
}: SimpleFieldProps) => {
  return (
    <div className={className}>
      <label className="label">
        <span className="label-text">
          {label}
          {required && ' *'}
        </span>
      </label>
      <input
        type={type}
        name={name}
        value={value}
        onInput={(e: any) => onChange(name, e.target.value)}
        className="input input-bordered w-full"
        placeholder={placeholder}
        required={required}
        step={step}
        min={min}
        max={max}
      />
    </div>
  );
};