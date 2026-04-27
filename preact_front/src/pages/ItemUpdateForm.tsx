// src/pages/ItemUpdateForm.tsx
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { apiClient } from '../lib/apiClient';
import { FormBuilder } from '../forms/FormBuilder';
import { useLanguage } from '../contexts/LanguageContext';
import { submitItemForm } from '../lib/itemSubmit';

export const ItemUpdateForm = ({ onClose }: { onClose: () => void }) => {
  const { url } = useLocation();
  const id = parseInt(url.split('/').pop() || '0');
  const lang = useLanguage().language;
  const [formData, setFormData] = useState<any>({});
  const [loadingData, setLoadingData] = useState(true);

  useEffect(() => {
    apiClient(`/preact/${id}`, { method: 'GET' })
      .then(data => {
        setFormData(data); // Просто сохраняем данные как есть!
        setLoadingData(false);
      })
      .catch(err => {
        console.error('Error loading item:', err);
        setLoadingData(false);
      });
  }, [id]);

  const handleChange = (name: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  const makeLoader = (endpoint: string) => async (search: string, page: number) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: '50',
      sort: 'name', // Добавляем сортировку по имени на сервере
      order: 'asc'  // От А до Я
    });

    // Если пользователь что-то ищет, добавляем поисковый запрос
    if (search) {
      params.append('search', search);
    }

    const response = await apiClient(`/handbooks_page/${endpoint}/${lang}?${params}`, { method: 'GET' });

    return {
      items: response.items || response,
      total: response.total || response.length
    };
  };

  if (loadingData) {
    return h('div', { style: { position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1500 }}, h('div', { style: { backgroundColor: 'white', padding: '20px', borderRadius: '8px' } }, 'Loading...'));
  }

  // 👇 ОБРАБОТЧИК SAVE
  const handleSave = async (e: Event) => {
    e.preventDefault();
    try {
      await submitItemForm(formData, id);
      alert('Item updated successfully!');
      onClose(); // Закрываем модалку
    } catch (err: any) {
      console.error(err);
      alert('Failed to save item: ' + err.message);
    }
  };

  const form = new FormBuilder(formData, handleChange);

  // ВОТ ТЕПЕРЬ ОДНОЙ СТРОКОЙ! Добавляйте или удаляйте только здесь:
  form
    .group('English', (b) => b
        .text('title', 'Title*')
        .text('subtitle', 'Subtitle')
        .textarea('description', 'Description', 5)
        .textarea('recommendation', 'Recommendation', 5)
        .textarea('madeof', 'Made of', 3)
        .text('anno', 'Anno')
    )
    .group('Русский', (b) => b
        .text('title_ru', 'Наименование')
        .text('subtitle_ru', 'Subtitle')
        .textarea('description_ru', 'Description', 5)
        .textarea('recommendation_ru', 'Recommendation', 5)
        .textarea('madeof_ru', 'Made of', 3)
        .text('anno', 'Anno')
    )
    .group('Fracaise', (b) => b
        .text('title_fr', 'Title*')
        .text('subtitle_fr', 'Subtitle')
        .textarea('description_fr', 'Description', 5)
        .textarea('recommendation_fr', 'Recommendation', 5)
        .textarea('madeof_fr', 'Made of', 3)
        .text('anno', 'Anno')
    )
    .group('Deutchland', (b) => b
        .text('title_de', 'Title*')
        .text('subtitle_de', 'Subtitle')
        .textarea('description_de', 'Description', 5)
        .textarea('recommendation_de', 'Recommendation', 5)
        .textarea('madeof_de', 'Made of', 3)
        .text('anno', 'Anno')
    )
    .group('Español', (b) => b
        .text('title_es', 'Title')
        .text('subtitle_es', 'Subtitle')
        .textarea('description_es', 'Description', 5)
        .textarea('recommendation_es', 'Recommendation', 5)
        .textarea('madeof_es', 'Made of', 3)
        .text('anno', 'Anno')
    )
    .group('Italiano', (b) => b
        .text('title_it', 'Title')
        .text('subtitle_it', 'Subtitle')
        .textarea('description_it', 'Description', 5)
        .textarea('recommendation_it', 'Recommendation', 5)
        .textarea('madeof_it', 'Made of', 3)
        .text('anno', 'Anno')
    )
    .group('中國人', (b) => b
        .text('title_zh', 'Title')
        .text('subtitle_zh', 'Subtitle')
        .textarea('description_zh', 'Description', 5)
        .textarea('recommendation_zh', 'Recommendation', 5)
        .textarea('madeof_zh', 'Made of', 3)
        .text('anno', 'Anno')
    )
    .group('Category & Classication', (c) => c
        .lazySelect('subcategory_id', 'Category', makeLoader('subcategories'), true)
        .lazySelect('classification_id', 'Classification', makeLoader('classifications'))
        .lazySelect('vintageconfig_id', 'Vintage configuration', makeLoader('vintageconfigs'))
        .lazySelect('designation_id', 'Designation', makeLoader('designations'))
    )
    .group('Locations & Producers', (e) => e
        .lazySelect('site_id', 'Country, Region, Subregion, Site', makeLoader('sites'), true)
        .lazySelect('parcel_id', 'Parcel', makeLoader('parcels'))
    )

    .group('General data', (d) => d
        .text('display_name', 'Display Name')
        .text('lwin', 'Liv-ex Wine Identification Number')
        .text('vol', 'Volume')
        .text('alc', 'Alcohol')
        .text('first_vintage', 'First vintage')
        .text('last_vintage', 'Last vintage')
        .lazySelect('source_id', 'Source', makeLoader('sources'))

    )
    .lazyCheckbox('foods', 'Foods', makeLoader('foods'))
    .lazyCheckbox('varietals', 'Varietals', makeLoader('varietals'), (id, isChecked, currentValue, onChange) => {
          // Тут можно отрендерить инпут для процентов, если галочка стоит!
          if (!isChecked) return null;
          return h('input', { type: 'number', className: 'input input-xs input-bordered w-16 ml-2', placeholder: '%' });
        })
    .imageGallery('images', 'Item Images', id, 5); // Позволит загрузить до 5 штук
  return h('div', { style: { position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1500 }},
    h('div', { style: { backgroundColor: 'white', padding: '20px', borderRadius: '8px', maxWidth: '1200px', width: '95%', maxHeight: '90vh', overflowY: 'auto' }},
      h('h2', { className: 'text-2xl font-bold mb-4' }, 'Update Item'),
      h('form', { onSubmit: handleSave },
        form.build(),
        h('div', { className: 'flex justify-end gap-4 mt-6' },
          h('button', { type: 'button', onClick: onClose, className: 'btn btn-ghost' }, 'Cancel'),
          h('button', { type: 'submit', className: 'btn btn-primary' }, 'Save')
        )
      )
    )
  );
};
