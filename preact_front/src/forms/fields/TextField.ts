// src/forms/fields/TextField.ts
import { h } from 'preact';
import { BaseField, FieldConfig } from './BaseField';

interface TextFieldConfig extends FieldConfig {
  type?: 'text' | 'number' | 'email';
  step?: string;
  min?: number;
  max?: number;
  placeholder?: string;
}

export class TextField extends BaseField<string> {
  private type: string;
  private step?: string;
  private min?: number;
  private max?: number;
  private placeholder: string;

  constructor(config: TextFieldConfig, value: string, onChange: (name: string, value: any) => void) {
    super(config, value, onChange);
    this.type = config.type || 'text';
    this.step = config.step;
    this.min = config.min;
    this.max = config.max;
    this.placeholder = config.placeholder || config.label;
  }

  render() {
    return h('div', { key: this.config.name, className: 'mb-4' },
      h('label', { className: 'label' },
        h('span', { className: 'label-text' },
          this.config.label,
          this.config.required && h('span', { className: 'text-red-500 ml-1' }, '*')
        )
      ),
      h('input', {
        type: this.type,
        name: this.config.name,
        value: this.value || '',
        onInput: (e: any) => this.handleChange(e.target.value),
        className: 'input input-bordered w-full',
        placeholder: this.placeholder,
        step: this.step,
        min: this.min,
        max: this.max,
        required: this.config.required
      })
    );
  }
}