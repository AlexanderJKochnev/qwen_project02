// src/utils/formUtils.ts
import { LANGUAGES, MULTILINGUAL_FIELDS } from '../config/itemFields';

export const generateInitialFormState = () => {
  const state: any = {
    subcategory_id: '',
    source_id: '',
    site_id: '',
    varietals: [] as string[],
    foods: [] as string[],
    file: null as File | null,
    drink_id: 0,
    id: 0,
    image_id: '',
    image_path: '',
    count: 0,
    alc: '',
    sugar: '',
    vol: '',
    price: '',
    age: ''
  };

  Object.keys(MULTILINGUAL_FIELDS).forEach(fieldName => {
    LANGUAGES.forEach(lang => {
      const key = lang === '' ? fieldName : `${fieldName}_${lang}`;
      state[key] = '';
    });
  });

  return state;
};

export const mapApiDataToForm = (apiData: any) => {
  const formData = generateInitialFormState();

  // Копируем ВСЕ поля из API
  Object.keys(formData).forEach(key => {
    if (apiData[key] !== undefined && apiData[key] !== null) {
      formData[key] = apiData[key];
    }
  });

  // Конвертируем числа в строки для input fields
  ['alc', 'sugar', 'vol', 'price'].forEach(field => {
    if (formData[field] !== undefined && formData[field] !== null) {
      formData[field] = formData[field].toString();
    }
  });

  // Конвертируем ID в строки для select
  ['subcategory_id', 'source_id', 'site_id'].forEach(field => {
    if (formData[field] !== undefined && formData[field] !== null) {
      formData[field] = formData[field].toString();
    }
  });

  // Обрабатываем varietals (приходят как массив объектов {id, percentage})
  if (apiData.varietals && Array.isArray(apiData.varietals)) {
    formData.varietals = apiData.varietals.map((v: any) => `${v.id}:${v.percentage || 100}`);
  } else {
    formData.varietals = [];
  }

  // Обрабатываем foods (приходят как массив объектов {id} или просто ids)
  if (apiData.foods && Array.isArray(apiData.foods)) {
    formData.foods = apiData.foods.map((f: any) => f.id?.toString() || f.toString());
  } else {
    formData.foods = [];
  }

  return formData;
};

export const prepareSubmitData = (formData: any) => {
  const submitData: any = { ...formData };

  // Удаляем файл из данных
  delete submitData.file;

  // Конвертируем строки в числа
  if (submitData.alc) submitData.alc = parseFloat(submitData.alc);
  if (submitData.sugar) submitData.sugar = parseFloat(submitData.sugar);
  if (submitData.vol) submitData.vol = parseFloat(submitData.vol);
  if (submitData.price) submitData.price = parseFloat(submitData.price);

  // Конвертируем ID
  if (submitData.subcategory_id) submitData.subcategory_id = parseInt(submitData.subcategory_id);
  if (submitData.site_id) submitData.site_id = parseInt(submitData.site_id);
  if (submitData.source_id) submitData.source_id = parseInt(submitData.source_id);

  // Обрабатываем varietals
  submitData.varietals = submitData.varietals.map((v: string) => {
    const [id, percentage] = v.split(':');
    return { id: parseInt(id), percentage: parseFloat(percentage) };
  });

  // Обрабатываем foods
  submitData.foods = submitData.foods.map((f: string) => ({ id: parseInt(f) }));

  return submitData;
};