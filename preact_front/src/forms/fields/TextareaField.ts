// src/forms/fields/TextareaField.ts
import { h } from 'preact';
import { BaseField, FieldConfig } from './BaseField';

export class TextareaField extends BaseField<string> {
  private rows: number;
  private placeholder: string;

  constructor(config: FieldConfig, value: string, onChange: (name: string, value: any) => void, rows = 3) {
    super(config, value, onChange);
    this.rows = rows;
    this.placeholder = config.label;
  }

  render() {
    return h('div', { key: this.config.name, className: 'mb-4' },
      h('label', { className: 'label' },
        h('span', { className: 'label-text' }, this.config.label)
      ),
      h('textarea', {
        name: this.config.name,
        value: this.value || '',
        onInput: (e: any) => this.handleChange(e.target.value),
        className: 'textarea textarea-bordered w-full',
        rows: this.rows,
        placeholder: this.placeholder
      })
    );
  }
}