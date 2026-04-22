// src/components/SimpleField.tsx
import { h } from 'preact';

interface SimpleFieldProps {
  name: string;
  label: string;
  type?: 'text' | 'number';
  value: string | number;
  onChange: (name: string, value: string) => void;
  step?: string;
  min?: number;
  max?: number;
}

export const SimpleField = ({ name, label, type = 'text', value, onChange, step, min, max }: SimpleFieldProps) => (
  <div>
    <label className="label">
      <span className="label-text">{label}</span>
    </label>
    <input
      type={type}
      name={name}
      value={value}
      onInput={(e: any) => onChange(name, e.target.value)}
      className="input input-bordered w-full"
      step={step}
      min={min}
      max={max}
    />
  </div>
);