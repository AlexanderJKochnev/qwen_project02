// src/utils/formUtils.ts
// утилиты для работы с формой
import { LANGUAGES, MULTILINGUAL_FIELDS } from '../config/itemFields';

// Генерация начального состояния формы из конфига
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
    count: 0
  };

  // Добавляем мультиязычные поля
  Object.keys(MULTILINGUAL_FIELDS).forEach(fieldName => {
    LANGUAGES.forEach(lang => {
      const key = lang === '' ? fieldName : `${fieldName}_${lang}`;
      state[key] = '';
    });
  });

  return state;
};

// Преобразование данных из API в форму
export const mapApiDataToForm = (apiData: any) => {
  const formData = generateInitialFormState();

  // Заполняем базовые поля
  Object.keys(formData).forEach(key => {
    if (apiData[key] !== undefined && apiData[key] !== null) {
      formData[key] = apiData[key];
    }
  });

  // Специальная обработка для массивов
  formData.varietals = (apiData.varietals || []).map((v: any) => `${v.id}:${v.percentage}`);
  formData.foods = (apiData.foods || []).map((f: any) => f.id.toString());

  return formData;
};

// Сбор данных для отправки на сервер
export const prepareSubmitData = (formData: any) => {
  const submitData: any = { ...formData };

  // Преобразуем числовые поля
  ['alc', 'sugar', 'vol', 'price'].forEach(field => {
    if (submitData[field]) {
      submitData[field] = parseFloat(submitData[field]);
    } else {
      delete submitData[field];
    }
  });

  // Преобразуем ID полей
  ['subcategory_id', 'site_id'].forEach(field => {
    if (submitData[field]) {
      submitData[field] = parseInt(submitData[field]);
    }
  });

  if (submitData.source_id) {
    submitData.source_id = parseInt(submitData.source_id);
  }

  // Обрабатываем varietals и foods
  submitData.varietals = submitData.varietals
    .map((v: string) => {
      const [id, percentage] = v.split(':');
      return { id: parseInt(id), percentage: parseFloat(percentage) };
    })
    .filter((v: any) => !isNaN(v.id) && !isNaN(v.percentage));

  submitData.foods = submitData.foods
    .map((f: string) => {
      const id = parseInt(f);
      return isNaN(id) ? null : { id };
    })
    .filter((f: any) => f !== null);

  // Удаляем временные поля
  delete submitData.file;
  delete submitData.image_path;
  delete submitData.image_id;

  return submitData;
};