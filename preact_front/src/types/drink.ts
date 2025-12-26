// src/types/drink.ts
import { BaseRead } from './base';

export interface LangFields {
  title?: string;
  subtitle?: string;
  description?: string;
  recommendation?: string;
  madeof?: string;
  alc?: string;    // сериализовано как "13%"
  sugar?: string;  // сериализовано как "5%"
  age?: string;
  sparkling?: boolean;
  pairing?: string[];
  varietal?: string[];
}

export interface DrinkReadFlat extends BaseRead {
  category: string;
  country: string;
  sparkling: boolean;
  en: LangFields;
  ru: LangFields;
  fr: LangFields;
  es: LangFields;
  de: LangFields;
}