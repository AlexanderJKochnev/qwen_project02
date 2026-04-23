// src/forms/fields/MultilingualFieldGroup.ts
import { h } from 'preact';
import { BaseField } from './BaseField';
import { TextField } from './TextField';
import { TextareaField } from './TextareaField';

interface MultilingualConfig {
  baseName: string;
  label: string;
  languages: string[];
  isTextarea?: boolean;
}

export class MultilingualFieldGroup extends BaseField<Record<string, string>> {
  private fields: BaseField<any>[];
  private isTextarea: boolean;

  constructor(config: MultilingualConfig, values: Record<string, string>, onChange: (name: string, value: any) => void) {
    super({ name: config.baseName, label: config.label }, values, onChange);
    this.isTextarea = config.isTextarea || false;

    // Создаем поля для каждого языка
    this.fields = config.languages.map(lang => {
      const fieldName = lang === 'base' ? config.baseName : `${config.baseName}_${lang}`;
      const fieldLabel = lang === 'base' ? config.label : `${config.label} (${lang.toUpperCase()})`;

      if (this.isTextarea) {
        return new TextareaField(
          { name: fieldName, label: fieldLabel },
          values[fieldName] || '',
          onChange
        );
      } else {
        return new TextField(
          { name: fieldName, label: fieldLabel },
          values[fieldName] || '',
          onChange
        );
      }
    });
  }

  render() {
    return h('details', { className: 'card bg-base-100 shadow mb-4' },
      h('summary', { className: 'p-4 font-bold' }, this.config.label),
      h('div', { className: 'card-body' },
        this.fields.map(field => field.render())
      )
    );
  }
}