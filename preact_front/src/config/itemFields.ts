// src/config/itemFields.ts
// конфигурация полей
export const LANGUAGES = ['', 'ru', 'fr', 'es', 'it', 'de', 'zh'] as const;
export type Language = typeof LANGUAGES[number];

export const MULTILINGUAL_FIELDS = {
  title: {
    label: 'Title',
    required: true,
    placeholder: {
      '': 'Title',
      ru: 'Заголовок на Русском',
      fr: 'Titre en Français',
      es: 'Título en español',
      it: 'Titolo',
      de: 'Titel',
      zh: '標題'
    }
  },
  subtitle: {
    label: 'Subtitle',
    required: false,
    placeholder: {
      '': 'Subtitle',
      ru: 'Подзаголовок',
      fr: 'Sous-titre',
      es: 'Subtítulo',
      it: 'Sottotitolo',
      de: 'Untertitel',
      zh: '副標題'
    }
  },
  description: {
    label: 'Description',
    required: false,
    placeholder: {
      '': 'Description',
      ru: 'Описание',
      fr: 'Description',
      es: 'Descripción',
      it: 'Descrizione',
      de: 'Beschreibung',
      zh: '描述'
    },
    isTextarea: true
  },
  recommendation: {
    label: 'Recommendation',
    required: false,
    placeholder: {
      '': 'Recommendation',
      ru: 'Рекомендация',
      fr: 'Recommandation',
      es: 'Recomendación',
      it: 'Raccomandazione',
      de: 'Empfehlung',
      zh: '推薦'
    },
    isTextarea: true
  },
  madeof: {
    label: 'Made Of',
    required: false,
    placeholder: {
      '': 'Made of',
      ru: 'Сделано из',
      fr: 'Fait de',
      es: 'Hecho de',
      it: 'Fatto di',
      de: 'Hergestellt aus',
      zh: '製成'
    },
    isTextarea: true
  }
} as const;

export const SIMPLE_FIELDS = [
  { name: 'vol', label: 'Volume', type: 'number', step: '0.01' },
  { name: 'price', label: 'Price', type: 'number', step: '0.01' },
  { name: 'alc', label: 'Alcohol (%)', type: 'number', step: '0.01', min: 0, max: 100 },
  { name: 'sugar', label: 'Sugar (%)', type: 'number', step: '0.01', min: 0, max: 100 },
  { name: 'age', label: 'Age', type: 'text' }
] as const;