// src/forms/fields/BaseField.ts
import { h } from 'preact';

export interface FieldConfig {
  name: string;
  label: string;
  required?: boolean;
}

export abstract class BaseField<T = any> {
  protected config: FieldConfig;
  protected value: T;
  protected onChange: (name: string, value: any) => void;

  constructor(config: FieldConfig, value: T, onChange: (name: string, value: any) => void) {
    this.config = config;
    this.value = value;
    this.onChange = onChange;
  }

  abstract render(): h.JSX.Element;

  protected handleChange(value: T) {
    this.onChange(this.config.name, value);
  }
}