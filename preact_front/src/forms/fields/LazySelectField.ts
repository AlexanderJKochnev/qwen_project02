// src/forms/fields/LazySelectField.ts
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { BaseField, FieldConfig } from './BaseField';

export interface LazySelectConfig extends FieldConfig {
  loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
}

export class LazySelectField extends BaseField<string> {
  private loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;

  constructor(config: LazySelectConfig, value: any, onChange: (name: string, value: any) => void) {
    // Принудительно кастуем в строку, чтобы избежать багов с числами
    const stringValue = (value !== null && value !== undefined) ? String(value) : '';
    super(config, stringValue, onChange);
    this.loadOptions = config.loadOptions;
  }

  private getDisplayName(item: any): string {
    return item.name || item.name_en || item.name_ru || item.name_fr ||
           item.name_es || item.name_it || item.name_de || item.name_zh || '';
  }

  render() {
    return h(NativeLazySelect, {
      name: this.config.name,
      label: this.config.label,
      value: this.value || '',
      required: this.config.required,
      loadOptions: this.loadOptions,
      getDisplayName: this.getDisplayName,
      onChange: (val: string) => this.handleChange(val)
    });
  }
}

interface NativeProps {
  name: string;
  label: string;
  value: string;
  required?: boolean;
  loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
  getDisplayName: (item: any) => string;
  onChange: (value: string) => void;
}

const NativeLazySelect = ({ name, label, value, required, loadOptions, getDisplayName, onChange }: NativeProps) => {
  const [options, setOptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    loadOptions('', 1)
      .then(result => {
        setOptions(result.items || []);
      })
      .catch(err => {
        console.error('Failed to load options:', err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return h('div', { className: 'mb-4', key: name },
    h('label', { className: 'label' },
      h('span', { className: 'label-text font-medium' },
        label,
        required && h('span', { className: 'text-red-500 ml-1' }, '*')
      )
    ),
    h('select', {
      name: name,
      value: value,
      onChange: (e: any) => onChange(e.target.value),
      className: 'select select-bordered w-full',
      required: required
    },
      h('option', { value: '' }, loading ? 'Loading...' : `Select ${label.toLowerCase()}`),
      options.map(option =>
        h('option', { key: option.id, value: String(option.id) }, getDisplayName(option))
      )
    )
  );
};
