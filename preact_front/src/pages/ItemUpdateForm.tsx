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
        setFormData({
          ...data,
          subcategory_id: data.subcategory_id?.toString() || '',
          brand_id: data.brand_id?.toString() || '',
          country_id: data.country_id?.toString() || '',
        });
        setLoadingData(false);
      });
  }, [id]);

  const handleChange = (name: string, value: any) => {
    setFormData((prev: any) => ({ ...prev, [name]: value }));
  };

  // 1. Универсальный генератор загрузок, чтобы не дублировать код
  const makeLoader = (endpoint: string) => async (search: string, page: number) => {
    const params = new URLSearchParams({ page: page.toString(), page_size: '50', ...(search && { search }) });
    const response = await apiClient(`/handbooks_page/${endpoint}/${lang}?${params}`, { method: 'GET' });
    return { items: response.items || response, total: response.total || response.length };
  };

  if (loadingData) return h('div', {}, 'Loading...');

  const form = new FormBuilder(formData, handleChange);

  // 2. Построение формы в цепочку. Добавляйте новые селекты одной строкой!
  form
    .text('title', 'Title')
    .lazySelect('subcategory_id', 'Subcategory', makeLoader('subcategories'), true)
    .lazySelect('brand_id', 'Brand', makeLoader('brands'))
    .lazySelect('country_id', 'Country', makeLoader('countries'))
    .lazySelect('manufacturer_id', 'Manufacturer', makeLoader('manufacturers'));

  return h('div', { className: 'fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-[1500]' },
    h('div', { className: 'bg-white p-6 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto' },
      h('h2', { className: 'text-2xl font-bold mb-4' }, 'Update Item'),
      h('form', { onSubmit: (e) => { e.preventDefault(); console.log(formData); } },
        form.build(),
        h('div', { className: 'flex justify-end gap-4 mt-6' },
          h('button', { type: 'button', onClick: onClose, className: 'btn btn-ghost' }, 'Cancel'),
          h('button', { type: 'submit', className: 'btn btn-primary' }, 'Save')
        )
      )
    )
  );
};
