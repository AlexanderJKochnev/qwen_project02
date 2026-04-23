// src/pages/ItemUpdateForm.tsx - НОВАЯ ВЕРСИЯ (чистый код)
import { h, useState, useEffect } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { apiClient } from '../lib/apiClient';
import { useLanguage } from '../contexts/LanguageContext';
import { ItemImage } from '../components/ItemImage';
import { FormBuilder } from '../forms/FormBuilder';

export const ItemUpdateForm = ({ onClose, onUpdated }: ItemUpdateFormProps) => {
  const { url } = useLocation();
  const id = parseInt(url.split('/').pop() || '0');
  const { language } = useLanguage();

  const [formData, setFormData] = useState<any>({});
  const [drinkAction, setDrinkAction] = useState<'update' | 'create'>('update');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [handbooks, setHandbooks] = useState<any>({
    subcategories: [], source: [], sites: [], varietals: [], foods: []
  });

  // Загрузка справочников
  useEffect(() => {
    Promise.all([
      apiClient(`/handbooks/subcategories/${language}`),
      apiClient(`/handbooks/source/${language}`),
      apiClient(`/handbooks/sites/${language}`),
      apiClient('/handbooks/varietals/all'),
      apiClient('/handbooks/foods/all')
    ]).then(([subcategories, source, sites, varietals, foods]) => {
      setHandbooks({ subcategories, source, sites, varietals, foods });
    });
  }, [language]);

  // Загрузка данных
  useEffect(() => {
    if (handbooks.varietals.length === 0) return;

    apiClient(`/preact/${id}`).then(data => {
      setFormData({
        ...data,
        subcategory_id: data.subcategory_id?.toString() || '',
        source_id: data.source_id?.toString() || '',
        site_id: data.site_id?.toString() || '',
        alc: data.alc?.toString() || '',
        sugar: data.sugar?.toString() || '',
        vol: data.vol?.toString() || '',
        price: data.price?.toString() || '',
        varietals: (data.varietals || []).map((v: any) => `${v.id}:${v.percentage}`),
        foods: (data.foods || []).map((f: any) => f.id.toString())
      });
      setLoadingData(false);
    });
  }, [id, handbooks.varietals.length]);

  const handleChange = (name: string, value: any) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setLoading(true);
    // ... логика отправки (без изменений)
  };

  if (loadingData) return <div>Loading...</div>;

  // ДЕКЛАРАТИВНОЕ ОПИСАНИЕ ФОРМЫ - 30 строк вместо 800!
  const form = new FormBuilder(formData, handleChange);

  return (
    <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1500 }}>
      <div style={{ background: 'white', padding: 20, borderRadius: 8, maxWidth: 800, width: '90%', maxHeight: '90vh', overflow: 'auto' }}>
        <h2>Update Item</h2>

        <form onSubmit={handleSubmit}>
          {/* Drink Action */}
          <div className="mb-4 p-4 border rounded">
            <label><input type="radio" checked={drinkAction === 'update'} onChange={() => setDrinkAction('update')} /> Update</label>
            <label className="ml-4"><input type="radio" checked={drinkAction === 'create'} onChange={() => setDrinkAction('create')} /> Create New</label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Левая колонка */}
            <div>
              {form
                .multilingual('title', 'Title', ['base', 'ru', 'fr', 'es', 'it', 'de', 'zh'])
                .multilingual('subtitle', 'Subtitle', ['base', 'ru', 'fr', 'es', 'it', 'de', 'zh'])
                .text('vol', 'Volume', { type: 'number', step: '0.01' })
                .text('price', 'Price', { type: 'number', step: '0.01' })
                .file('file', 'Image')
                .build()
              }
              {formData.image_path && !formData.file && <ItemImage image_id={formData.image_id} size="medium" />}
            </div>

            {/* Правая колонка */}
            <div>
              {form
                .select('subcategory_id', 'Subcategory', handbooks.subcategories, true)
                .select('source_id', 'Source', handbooks.source)
                .select('site_id', 'Site', handbooks.sites, true)
                .text('alc', 'Alcohol %', { type: 'number', step: '0.01', min: 0, max: 100 })
                .text('sugar', 'Sugar %', { type: 'number', step: '0.01', min: 0, max: 100 })
                .text('age', 'Age')
                .build()
              }
            </div>

            {/* Полная ширина */}
            {form
              .multilingual('description', 'Description', ['base', 'ru', 'fr', 'es', 'it', 'de', 'zh'], true)
              .multilingual('recommendation', 'Recommendation', ['base', 'ru', 'fr', 'es', 'it', 'de', 'zh'], true)
              .multilingual('madeof', 'Made Of', ['base', 'ru', 'fr', 'es', 'it', 'de', 'zh'], true)
              .build()
            }

            {/* Чекбоксы с дополнительной логикой */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {new CheckboxGroupField(
                { name: 'varietals', label: 'Varietals', options: handbooks.varietals,
                  renderExtra: (id, isChecked, currentValue, onChange) => {
                    if (!isChecked) return null;
                    const percentage = currentValue.find((v: string) => v.startsWith(`${id}:`))?.split(':')[1] || '100';
                    return h('input', {
                      type: 'number',
                      value: percentage,
                      onInput: (e: any) => {
                        const newValue = currentValue.map((v: string) =>
                          v.startsWith(`${id}:`) ? `${id}:${e.target.value}` : v
                        );
                        onChange(newValue);
                      },
                      className: 'input input-bordered w-20 ml-2',
                      placeholder: '%'
                    });
                  }
                },
                formData.varietals || [],
                handleChange
              ).render()}

              {new CheckboxGroupField(
                { name: 'foods', label: 'Foods', options: handbooks.foods },
                formData.foods || [],
                handleChange
              ).render()}
            </div>
          </div>

          <div className="flex justify-end gap-4 mt-6">
            <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Updating...' : 'Update Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};