// src/components/MultilingualField.tsx
// переиспользуемые компоненты
import { h } from 'preact';
import { LANGUAGES, MULTILINGUAL_FIELDS } from '../config/itemFields';

interface MultilingualFieldProps {
  fieldName: keyof typeof MULTILINGUAL_FIELDS;
  values: Record<string, string>;
  onChange: (name: string, value: string) => void;
  className?: string;
}

export const MultilingualField = ({ fieldName, values, onChange, className = '' }: MultilingualFieldProps) => {
  const config = MULTILINGUAL_FIELDS[fieldName];
  const Component = config.isTextarea ? 'textarea' : 'input';

  return (
    <details className={className}>
      <summary>{config.label}</summary>
      <div className="card-body">
        {LANGUAGES.map(lang => {
          const key = lang === '' ? fieldName : `${fieldName}_${lang}`;
          const placeholder = config.placeholder[lang as keyof typeof config.placeholder];
          const label = lang === '' ? config.label : `${config.label} (${lang.toUpperCase()})`;

          return (
            <div key={key}>
              <label className="label">
                <span className="label-text">{label}</span>
              </label>
              <Component
                name={key}
                value={values[key] || ''}
                onInput={(e: any) => onChange(key, e.target.value)}
                className={`${config.isTextarea ? 'textarea' : 'input'} input-bordered w-full`}
                placeholder={placeholder}
                rows={config.isTextarea ? 3 : undefined}
                required={config.required && lang === ''}
              />
            </div>
          );
        })}
      </div>
    </details>
  );
};