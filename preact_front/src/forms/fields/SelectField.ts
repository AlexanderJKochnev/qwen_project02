// src/forms/fields/SelectField.ts
import { h } from 'preact';
import { BaseField, FieldConfig } from './BaseField';

interface SelectOption {
  id: number;
  name: string;
  [key: string]: any;
}

export class SelectField extends BaseField<string> {
  private options: SelectOption[];
  private placeholder: string;

  constructor(config: FieldConfig, value: string, options: SelectOption[], onChange: (name: string, value: any) => void) {
    super(config, value, onChange);
    this.options = options;
    this.placeholder = `Select ${config.label.toLowerCase()}`;
  }

  private getDisplayName(option: SelectOption): string {
    return option.name || option.name_en || option.name_ru || option.name_fr ||
           option.name_es || option.name_it || option.name_de || option.name_zh || '';
  }

  render() {
    return h('div', { key: this.config.name, className: 'mb-4' },
      h('label', { className: 'label' },
        h('span', { className: 'label-text' },
          this.config.label,
          this.config.required && h('span', { className: 'text-red-500 ml-1' }, '*')
        )
      ),
      h('select', {
        name: this.config.name,
        value: this.value || '',
        onChange: (e: any) => this.handleChange(e.target.value),
        className: 'select select-bordered w-full',
        required: this.config.required
      },
        h('option', { value: '' }, this.placeholder),
        this.options.map(option =>
          h('option', { key: option.id, value: option.id }, this.getDisplayName(option))
        )
      )
    );
  }
}