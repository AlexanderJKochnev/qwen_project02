// src/forms/fields/CheckboxGroupField.ts
import { h } from 'preact';
import { BaseField, FieldConfig } from './BaseField';

interface CheckboxOption {
  id: number;
  name: string;
  [key: string]: any;
}

interface CheckboxGroupConfig extends FieldConfig {
  options: CheckboxOption[];
  selectedIds: string[];
  renderExtra?: (id: string, isChecked: boolean, currentValue: any, onChange: (value: any) => void) => h.JSX.Element | null;
}

export class CheckboxGroupField extends BaseField<string[]> {
  private options: CheckboxOption[];
  private renderExtra?: CheckboxGroupConfig['renderExtra'];

  constructor(config: CheckboxGroupConfig, value: string[], onChange: (name: string, value: any) => void) {
    super(config, value, onChange);
    this.options = config.options;
    this.renderExtra = config.renderExtra;
  }

  private getDisplayName(option: CheckboxOption): string {
    return option.name || option.name_en || option.name_ru || option.name_fr ||
           option.name_es || option.name_it || option.name_de || option.name_zh || '';
  }

  private handleToggle(optionId: string, checked: boolean) {
    const newValue = checked
      ? [...this.value, optionId]
      : this.value.filter(id => id !== optionId);
    this.handleChange(newValue);
  }

  render() {
    const sortedOptions = [...this.options].sort((a, b) => {
      const aChecked = this.value.includes(a.id.toString());
      const bChecked = this.value.includes(b.id.toString());
      if (aChecked && !bChecked) return -1;
      if (!aChecked && bChecked) return 1;
      return this.getDisplayName(a).localeCompare(this.getDisplayName(b));
    });

    return h('div', { className: 'card bg-base-100 shadow mb-4' },
      h('details', {},
        h('summary', { className: 'p-4 font-bold' }, this.config.label),
        h('div', { className: 'border rounded-lg p-2 max-h-40 overflow-y-auto' },
          sortedOptions.map(option => {
            const optionId = option.id.toString();
            const isChecked = this.value.includes(optionId);

            return h('div', { key: optionId, className: 'flex items-center mb-2' },
              h('input', {
                type: 'checkbox',
                id: `${this.config.name}-${optionId}`,
                checked: isChecked,
                onChange: (e: any) => this.handleToggle(optionId, e.target.checked),
                className: 'mr-2'
              }),
              h('label', {
                htmlFor: `${this.config.name}-${optionId}`,
                className: this.renderExtra ? 'flex-1 cursor-pointer' : 'cursor-pointer'
              }, this.getDisplayName(option)),
              this.renderExtra && this.renderExtra(optionId, isChecked, this.value, (newValue: any) => this.handleChange(newValue))
            );
          })
        )
      )
    );
  }
}