// src/forms/fields/FileField.ts
import { h } from 'preact';
import { BaseField, FieldConfig } from './BaseField';

export class FileField extends BaseField<File | null> {
  private accept: string;

  constructor(config: FieldConfig, value: File | null, onChange: (name: string, value: any) => void, accept = 'image/*') {
    super(config, value, onChange);
    this.accept = accept;
  }

  render() {
    return h('div', { className: 'mb-4' },
      h('label', { className: 'label' },
        h('span', { className: 'label-text' }, this.config.label)
      ),
      h('input', {
        type: 'file',
        name: this.config.name,
        onChange: (e: any) => this.handleChange(e.target.files?.[0] || null),
        className: 'file-input file-input-bordered w-full',
        accept: this.accept
      })
    );
  }
}