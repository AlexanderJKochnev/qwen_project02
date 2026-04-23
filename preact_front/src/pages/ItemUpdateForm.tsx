// src/pages/ItemUpdateForm.tsx - с select для subcategory
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { apiClient } from '../lib/apiClient';
import { FormBuilder } from '../forms/FormBuilder';
import { LazySelect } from '../components/LazySelect';

interface ItemUpdateFormProps {
  onClose: () => void;
  onUpdated?: () => void;
}

export const ItemUpdateForm = ({ onClose, onUpdated }: ItemUpdateFormProps) => {
  const { url } = useLocation();
  const id = parseInt(url.split('/').pop() || '0');

  const [formData, setFormData] = useState<any>({});
  const [drinkAction, setDrinkAction] = useState<'update' | 'create'>('update');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Загрузка данных элемента
  useEffect(() => {
    console.log('Loading item data for id:', id);

    apiClient(`/preact/${id}`, { method: 'GET' })
      .then(data => {
        console.log('Item data received:', data);

        setFormData({
          ...data,
          alc: data.alc?.toString() || '',
          vol: data.vol?.toString() || '',
          price: data.price?.toString() || '',
          sugar: data.sugar?.toString() || '',
          subcategory_id: data.subcategory_id?.toString() || '',
        });
        setLoadingData(false);
      })
      .catch(err => {
        console.error('Error loading item:', err);
        setError(err.message);
        setLoadingData(false);
      });
  }, [id]);

  const handleChange = (name: string, value: any) => {
    console.log('Field change:', name, value);
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Функция загрузки опций для subcategory с API
  const loadSubcategories = async (search: string, page: number) => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: '50',
      ...(search && { search })
    });

    const response = await apiClient(`/handbooks/subcategories?${params}`, { method: 'GET' });
    return {
      items: response.items || response,
      total: response.total || response.length
    };
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setLoading(true);

    try {
      console.log('Submit data:', formData);
      alert('Submit - пока только лог');
      setLoading(false);
    } catch (error) {
      console.error('Submit error:', error);
      setLoading(false);
    }
  };

  if (loadingData) {
    return h('div', {
      style: {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1500
      }
    },
      h('div', { style: { backgroundColor: 'white', padding: '20px', borderRadius: '8px' } },
        'Loading...'
      )
    );
  }

  if (error) {
    return h('div', {
      style: {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0,0,0,0.5)',
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        zIndex: 1500
      }
    },
      h('div', { style: { backgroundColor: 'white', padding: '20px', borderRadius: '8px' } },
        h('h2', {}, 'Error'),
        h('p', {}, error),
        h('button', { onClick: onClose, className: 'btn btn-ghost' }, 'Close')
      )
    );
  }

  // СОЗДАЕМ ФОРМУ
  const form = new FormBuilder(formData, handleChange);

  // Текстовые поля + один select с ленивой загрузкой
  form
    .text('title', 'Title')
    .text('title_ru', 'Title (Russian)')
    .text('title_fr', 'Title (French)')
    .textarea('description', 'Description')
    .textarea('description_ru', 'Description (Russian)')
    .textarea('description_fr', 'Description (French)')
    .text('vol', 'Volume (L)', { type: 'number', step: '0.01' })
    .text('alc', 'Alcohol (%)', { type: 'number', step: '0.1' });

  return h('div', {
    style: {
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1500
    }
  },
    h('div', {
      style: {
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '8px',
        maxWidth: '800px',
        width: '90%',
        maxHeight: '90vh',
        overflowY: 'auto'
      }
    },
      h('h2', {}, 'Update Item (Step 2 - With Lazy Select)'),

      // Drink Action
      h('div', { className: 'mb-4 p-4 border rounded-lg' },
        h('h3', { className: 'font-bold mb-2' }, 'Drink Action'),
        h('div', { className: 'flex gap-4' },
          h('label', { className: 'flex items-center' },
            h('input', {
              type: 'radio',
              checked: drinkAction === 'update',
              onChange: () => setDrinkAction('update')
            }),
            h('span', { className: 'ml-2' }, 'Update existing drink')
          ),
          h('label', { className: 'flex items-center' },
            h('input', {
              type: 'radio',
              checked: drinkAction === 'create',
              onChange: () => setDrinkAction('create')
            }),
            h('span', { className: 'ml-2' }, 'Save existing drink and create new')
          )
        )
      ),

      // Форма
      h('form', { onSubmit: handleSubmit },
        // Текстовые поля через FormBuilder
        form.build(),

        // Lazy Select для subcategory (добавляем вручную так как FormBuilder пока его не поддерживает)
        h(LazySelect, {
          name: 'subcategory_id',
          label: 'Subcategory',
          value: formData.subcategory_id || '',
          onChange: handleChange,
          loadOptions: loadSubcategories,
          required: true,
          pageSize: 50
        }),

        h('div', { className: 'flex justify-end gap-4 mt-6' },
          h('button', { type: 'button', onClick: onClose, className: 'btn btn-ghost', disabled: loading }, 'Cancel'),
          h('button', { type: 'submit', className: `btn btn-primary ${loading ? 'loading' : ''}`, disabled: loading },
            loading ? 'Updating...' : 'Update Item'
          )
        )
      ),

      // Debug
      h('details', { className: 'mt-4' },
        h('summary', {}, 'Debug: Form Data'),
        h('pre', { className: 'text-xs overflow-auto max-h-96' },
          JSON.stringify(formData, null, 2)
        )
      )
    )
  );
};