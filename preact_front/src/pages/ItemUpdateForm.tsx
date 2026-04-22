// src/pages/ItemUpdateForm.tsx (refactored)

import { h, useState, useEffect } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { apiClient } from '../lib/apiClient';
import { useLanguage } from '../contexts/LanguageContext';
import { ItemImage } from '../components/ItemImage';
import { MultilingualField } from '../components/MultilingualField';
import { SelectField } from '../components/SelectField';
import { CheckboxGroup } from '../components/CheckboxGroup';
import { SimpleField } from '../components/SimpleField';
import { generateInitialFormState, mapApiDataToForm, prepareSubmitData } from '../utils/formUtils';
import { MULTILINGUAL_FIELDS, SIMPLE_FIELDS } from '../config/itemFields';

export const ItemUpdateForm = ({ onClose, onUpdated }: ItemUpdateFormProps) => {
  const { url } = useLocation();
  const id = parseInt(url.split('/').pop() || '');
  const { language } = useLanguage();

  const [formData, setFormData] = useState(generateInitialFormState);
  const [drinkAction, setDrinkAction] = useState<'update' | 'create'>('update');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [handbooks, setHandbooks] = useState({
    subcategories: [], source: [], sites: [], varietals: [], foods: []
  });

  // Загрузка справочников (тот же код, но можно вынести в хук)
  useEffect(() => {
    const loadHandbooks = async () => { /* ... тот же код ... */ };
    loadHandbooks();
  }, [language]);

  // Загрузка данных элемента
  useEffect(() => {
    const loadItemData = async () => {
      if (handbooks.varietals.length === 0 || handbooks.foods.length === 0) return;

      try {
        setLoadingData(true);
        const data = await apiClient(`/preact/${id}`, { method: 'GET' });
        setFormData(mapApiDataToForm(data));
      } catch (err) {
        setError(`Failed to load item data: ${err.message}`);
      } finally {
        setLoadingData(false);
      }
    };

    loadItemData();
  }, [id, handbooks.varietals.length, handbooks.foods.length]);

  const handleFieldChange = (name: string, value: string) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (file: File | null) => {
    setFormData(prev => ({ ...prev, file }));
  };

  const handleCheckboxToggle = (field: 'varietals' | 'foods') => (id: string, checked: boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: checked
        ? [...prev[field], id]
        : prev[field].filter(i => i !== id)
    }));
  };

  const handleVarietalPercentage = (varietalId: string, percentage: string) => {
    setFormData(prev => ({
      ...prev,
      varietals: prev.varietals.map(v =>
        v.startsWith(`${varietalId}:`) ? `${varietalId}:${percentage}` : v
      )
    }));
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setLoading(true);

    try {
      const submitData = prepareSubmitData(formData);
      const multipartFormData = new FormData();
      multipartFormData.append('data', JSON.stringify({
        ...submitData,
        drink_action: drinkAction,
        drink_id: formData.drink_id,
        id: formData.id
      }));

      if (formData.file) {
        multipartFormData.append('file', formData.file);
      }

      await apiClient(`/items/update_item_drink/${id}`, {
        method: 'PATCH',
        body: multipartFormData
      }, false);

      onUpdated?.();
      onClose();
    } catch (error) {
      alert(`Error updating item: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Рендер (стал в 5 раз короче!)
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h2>Update Item</h2>

        {/* Drink Action */}
        <div className="mb-4 p-4 border rounded-lg">
          <h3 className="font-bold mb-2">Drink Action</h3>
          <div className="flex gap-4">
            <label><input type="radio" checked={drinkAction === 'update'}
              onChange={() => setDrinkAction('update')} /> Update existing</label>
            <label><input type="radio" checked={drinkAction === 'create'}
              onChange={() => setDrinkAction('create')} /> Create new</label>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* Basic Info Card */}
            <div className="card bg-base-100 shadow">
              <MultilingualField fieldName="title" values={formData} onChange={handleFieldChange} />
              <MultilingualField fieldName="subtitle" values={formData} onChange={handleFieldChange} />

              {SIMPLE_FIELDS.map(field => (
                <SimpleField key={field.name} {...field} value={formData[field.name]} onChange={handleFieldChange} />
              ))}

              {/* File upload */}
              <div>
                <label>File</label>
                <input type="file" onChange={e => handleFileChange((e.target as HTMLInputElement).files?.[0] || null)} />
              </div>

              {formData.image_path && !formData.file && (
                <ItemImage image_id={formData.image_id} size="medium" />
              )}
            </div>

            {/* Category Card */}
            <div className="card bg-base-100 shadow">
              <details><summary>Category and Location</summary>
                <div className="card-body">
                  <SelectField name="subcategory_id" label="Subcategory" value={formData.subcategory_id}
                    options={handbooks.subcategories} onChange={handleFieldChange} required />
                  <SelectField name="source_id" label="Source" value={formData.source_id}
                    options={handbooks.source} onChange={handleFieldChange} />
                  <SelectField name="site_id" label="Site" value={formData.site_id}
                    options={handbooks.sites} onChange={handleFieldChange} required />
                </div>
              </details>
            </div>

            {/* Multilingual Text Fields */}
            <MultilingualField fieldName="description" values={formData} onChange={handleFieldChange} className="card" />
            <MultilingualField fieldName="recommendation" values={formData} onChange={handleFieldChange} className="card" />
            <MultilingualField fieldName="madeof" values={formData} onChange={handleFieldChange} className="card" />

            {/* Checkbox Groups */}
            <div className="card">
              <CheckboxGroup title="Varietals" items={handbooks.varietals} selectedIds={formData.varietals.map(v => v.split(':')[0])}
                onToggle={handleCheckboxToggle('varietals')}
                renderExtra={(id, isChecked) => isChecked && (
                  <input type="number" placeholder="%" className="input input-bordered w-20 ml-2"
                    value={formData.varietals.find(v => v.startsWith(`${id}:`))?.split(':')[1] || '100'}
                    onChange={e => handleVarietalPercentage(id, (e.target as HTMLInputElement).value)} />
                )} />
            </div>

            <div className="card">
              <CheckboxGroup title="Foods" items={handbooks.foods} selectedIds={formData.foods}
                onToggle={handleCheckboxToggle('foods')} />
            </div>
          </div>

          {/* Buttons */}
          <div className="flex justify-end gap-4">
            <button type="button" onClick={onClose} className="btn btn-ghost">Cancel</button>
            <button type="submit" className={`btn btn-primary ${loading ? 'loading' : ''}`}>
              {loading ? 'Updating...' : 'Update Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};