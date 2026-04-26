// src/forms/FormBuilder.ts
import { h } from 'preact';
import { TextField } from './fields/TextField';
import { TextareaField } from './fields/TextareaField';
import { SelectField } from './fields/SelectField';
import { MultilingualFieldGroup } from './fields/MultilingualFieldGroup';
import { CheckboxGroupField } from './fields/CheckboxGroupField';
import { FileField } from './fields/FileField';
import { LazySelectField } from './fields/LazySelectField';
import { LazyCheckboxGroupField, LazyCheckboxConfig } from './fields/LazyCheckboxGroupField';
import { ImageGalleryField } from './fields/ImageGalleryField';

export class FormBuilder {
  private fields: h.JSX.Element[] = [];
  private formData: Record<string, any>;
  private onChange: (name: string, value: any) => void;

  constructor(formData: Record<string, any>, onChange: (name: string, value: any) => void) {
    this.formData = formData;
    this.onChange = onChange;
  }

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

  lazySelect(
    name: string,
    label: string,
    loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>,
    required?: boolean
  ) {
    this.fields.push(
      new LazySelectField({ name, label, required, loadOptions }, this.formData[name] || '', this.onChange).render()
    );
    return this;
  }

  multilingual(baseName: string, label: string, languages: string[], isTextarea = false) {
    this.fields.push(new MultilingualFieldGroup({ baseName, label, languages, isTextarea }, this.formData, this.onChange).render());
    return this;
  }

  lazyCheckbox(
    name: string,
    label: string,
    loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>,
    renderExtra?: LazyCheckboxConfig['renderExtra']
  ) {
    this.fields.push(
      new LazyCheckboxGroupField({ name, label, loadOptions, renderExtra }, this.formData[name] || [], this.onChange).render()
    );
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

  imageGallery(name: string, label: string, recordId: number, maxImages = 5) {
    this.fields.push(
      new ImageGalleryField({ name, label, recordId, maxImages }, this.formData[name], this.onChange).render()
    );
    return this;
  }

  // 🛡️ НАШ НОВЫЙ МЕТОД ДЛЯ ГРУППИРОВКИ
  group(title: string, callback: (builder: FormBuilder) => void) {
    // 1. Сохраняем ссылку на оригинальный массив полей
    const originalFields = this.fields;

    // 2. Подменяем массив на пустой, чтобы собрать только поля группы
    this.fields = [];

    // 3. Вызываем ваш коллбэк (наполняет подмененный пустой массив)
    callback(this);

    // 4. Оборачиваем собранные элементы в красивую плашку
    const groupElement = h('details', { className: 'card bg-base-100 shadow mb-4 border rounded-lg'},
      h('summary', { className: 'p-4 font-bold cursor-pointer bg-gray-50 border-b' }, title),
      h('div', { className: 'p-4 space-y-4' }, this.fields)
    );

    // 5. Возвращаем оригинальный массив и пушим в него готовую группу
    this.fields = [...originalFields, groupElement];

    return this; // Для цепочки вызовов
  }

  build() {
    return h('div', { className: 'space-y-4' }, this.fields);
  }
}
