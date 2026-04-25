// src/pages/ItemUpdateForm.tsx
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { apiClient } from '../lib/apiClient';
import { FormBuilder } from '../forms/FormBuilder';
import { useLanguage } from '../contexts/LanguageContext';

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

  const form = new FormBuilder(formData, handleChange);

  // ВОТ ТЕПЕРЬ ОДНОЙ СТРОКОЙ! Добавляйте или удаляйте только здесь:
  form
    .text('title', 'Title')
    .text('subtitle', 'Subtitle')
    .text('lwin', 'lwin')
    .lazySelect('subcategory_id', 'Subcategory', makeLoader('subcategories'), true)
    .lazySelect('source_id', 'Source', makeLoader('sources'))
    .lazySelect('site_id', 'Site', makeLoader('sites'))
    .lazySelect('producer_id', 'Producer', makeLoader('producers'))
    .lazyCheckbox('foods', 'Foods', makeLoader('foods'))
    .lazyCheckbox('varietals', 'Varietals', makeLoader('varietals'), (id, isChecked, currentValue, onChange) => {
      // Тут можно отрендерить инпут для процентов, если галочка стоит!
      if (!isChecked) return null;
      return h('input', { type: 'number', className: 'input input-xs input-bordered w-16 ml-2', placeholder: '%' });
    });
  return h('div', { style: { position: 'fixed', top: 0, left: 0, width: '100%', height: '100%', backgroundColor: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 1500 }},
    h('div', { style: { backgroundColor: 'white', padding: '20px', borderRadius: '8px', maxWidth: '1200px', width: '95%', maxHeight: '90vh', overflowY: 'auto' }},
      h('h2', { className: 'text-2xl font-bold mb-4' }, 'Update Item'),
      h('form', { onSubmit: (e) => { e.preventDefault(); console.log('Submitting:', formData); } },
        form.build(),
        h('div', { className: 'flex justify-end gap-4 mt-6' },
          h('button', { type: 'button', onClick: onClose, className: 'btn btn-ghost' }, 'Cancel'),
          h('button', { type: 'submit', className: 'btn btn-primary' }, 'Save')
        )
      )
    )
  );
};
