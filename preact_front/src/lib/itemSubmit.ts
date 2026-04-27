// src/lib/itemSubmit.ts

// Список ключей, которые требует бэкенд для JSON
const ALLOWED_KEYS = [
  'alc', 'subcategory_id', 'sweetness_id', 'title', 'title_ru', 'title_fr',
  'subtitle', 'subtitle_ru', 'subtitle_fr', 'description', 'description_ru',
  'description_fr', 'recommendation', 'recommendation_ru', 'recommendation_fr',
  'madeof', 'madeof_ru', 'madeof_fr', 'title_es', 'subtitle_es',
  'description_es', 'recommendation_es', 'madeof_es', 'title_it', 'subtitle_it',
  'description_it', 'recommendation_it', 'madeof_it', 'title_de', 'subtitle_de',
  'description_de', 'recommendation_de', 'madeof_de', 'title_zh', 'subtitle_zh',
  'description_zh', 'recommendation_zh', 'madeof_zh', 'source_id', 'producer_id',
  'vintageconfig_id', 'classification_id', 'designation_id', 'site_id', 'parcel_id',
  'first_vintage', 'last_vintage', 'lwin', 'anno', 'display_name', 'vol',
  'price', 'count'
];

/**
 * Универсальный обработчик отправки формы
 * @param formData - текущее состояние данных формы
 * @param recordId - ID записи (null или undefined для создания)
 */
export async function submitItemForm(formData: Record<string, any>, recordId?: number | null) {
  const formPayload = new FormData();
  const dataToEncode: Record<string, any> = {};

  // 1. Собираем только разрешенные ключи
  ALLOWED_KEYS.forEach(key => {
    if (formData[key] !== undefined) {
      dataToEncode[key] = formData[key];
    }
  });

  // 2. Если мы обновляем, добавляем ID в JSON
  if (recordId) {
    dataToEncode['id'] = recordId;
  }

  // 3. Упаковываем JSON в строку
  formPayload.append('data', JSON.stringify(dataToEncode));

  // 4. Проверяем наличие нового файла изображения
  if (Array.isArray(formData.images)) {
    const newImage = formData.images.find((img: any) => !img.isExisting && img.file);
    if (newImage) {
      formPayload.append('file', newImage.file);
    }
  }

  // 5. Вычисляем URL и Метод запроса
  // Если есть recordId -> POST (или PUT) на /update/{id}
  // Если нет recordId -> POST на эндпоинт создания (например, /create)
  const url = recordId ? `/items/update_item_drink/${recordId}` : `/items/create_item_drink/`;
  const token = localStorage.getItem('token');

  const response = await fetch(url, {
    method: recordId ? 'PATCH' : 'POST',
    headers: {
      'Authorization': `Bearer ${token || ''}`,
    },
    body: formPayload
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Server error: ${response.status} - ${errorText}`);
  }

  return await response.json();
}
