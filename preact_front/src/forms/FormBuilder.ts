// src/forms/FormBuilder.ts
import { h } from 'preact';
import { TextField } from './fields/TextField';
import { TextareaField } from './fields/TextareaField';
import { SelectField } from './fields/SelectField';
import { MultilingualFieldGroup } from './fields/MultilingualFieldGroup';
import { CheckboxGroupField } from './fields/CheckboxGroupField';
import { FileField } from './fields/FileField';

export class FormBuilder {
  private fields: h.JSX.Element[] = [];
  private formData: Record<string, any>;
  private onChange: (name: string, value: any) => void;

  constructor(formData: Record<string, any>, onChange: (name: string, value: any) => void) {
    this.formData = formData;
    this.onChange = onChange;
  }

  // ОДНА СТРОЧКА для создания поля
  text(name: string, label: string, options?: any) {
    this.fields.push(new TextField({ name, label, ...options }, this.formData[name] || '', this.onChange).render());
    return this;
  }

  textarea(name: string, label: string, rows?: number) {
    this.fields.push(new TextareaField({ name, label }, this.formData[name] || '', this.onChange, rows).render());
    return this;
  }

  select(name: string, label: string, options: any[], required?: boolean) {
    this.fields.push(new SelectField({ name, label, required }, this.formData[name] || '', options, this.onChange).render());
    return this;
  }

  multilingual(baseName: string, label: string, languages: string[], isTextarea = false) {
    this.fields.push(new MultilingualFieldGroup({ baseName, label, languages, isTextarea }, this.formData, this.onChange).render());
    return this;
  }

  checkboxGroup(name: string, label: string, options: any[], renderExtra?: any) {
    this.fields.push(new CheckboxGroupField({ name, label, options, renderExtra }, this.formData[name] || [], this.onChange).render());
    return this;
  }

  file(name: string, label: string) {
    this.fields.push(new FileField({ name, label }, this.formData[name] || null, this.onChange).render());
    return this;
  }

  build() {
    return h('div', { className: 'space-y-4' }, this.fields);
  }
}