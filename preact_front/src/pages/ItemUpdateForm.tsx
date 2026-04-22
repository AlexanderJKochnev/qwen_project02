// src/pages/ItemUpdateForm.tsx
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
import { SIMPLE_FIELDS } from '../config/itemFields';

export const ItemUpdateForm = ({ onClose, onUpdated }: ItemUpdateFormProps) => {
  const { url } = useLocation();
  const id = parseInt(url.split('/').pop() || '0');
  const { language } = useLanguage();

  const [formData, setFormData] = useState(generateInitialFormState);
  const [drinkAction, setDrinkAction] = useState<'update' | 'create'>('update');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [handbooks, setHandbooks] = useState({
    subcategories: [],
    source: [],
    sites: [],
    varietals: [],
    foods: []
  });

  // Загрузка справочников
  useEffect(() => {
    const loadHandbooks = async () => {
      try {
        const [subcategories, source, sites, varietals, foods] = await Promise.all([
          apiClient(`/handbooks/subcategories/${language}`),
          apiClient(`/handbooks/source/${language}`),
          apiClient(`/handbooks/sites/${language}`),
          apiClient('/handbooks/varietals/all'),
          apiClient('/handbooks/foods/all')
        ]);

        const sortByName = (items: any[]) => [...items].sort((a, b) => {
          const aName = a.name || a.name_en || a.name_ru || '';
          const bName = b.name || b.name_en || b.name_ru || '';
          return aName.localeCompare(bName);
        });

        setHandbooks({
          subcategories: sortByName(subcategories),
          source: sortByName(source),
          sites: sortByName(sites),
          varietals: sortByName(varietals),
          foods: sortByName(foods)
        });
      } catch (err) {
        console.error('Failed to load handbooks', err);
        setError('Failed to load handbook data');
      }
    };
    loadHandbooks();
  }, [language]);

  // Загрузка данных элемента - ВАЖНО: зависит от handbooks
  useEffect(() => {
    const loadItemData = async () => {
      if (handbooks.varietals.length === 0 || handbooks.foods.length === 0) return;

      try {
        setLoadingData(true);
        const data = await apiClient(`/preact/${id}`, { method: 'GET' });
        console.log('Loaded data:', data); // Для отладки
        const mappedData = mapApiDataToForm(data);
        console.log('Mapped data:', mappedData); // Для отладки
        setFormData(mappedData);
      } catch (err) {
        console.error('Failed to load item', err);
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

  if (loadingData) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0,0,0,0.5)',
        zIndex: 1500,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px' }}>
          <div className="flex justify-center items-center">
            <span className="loading loading-spinner loading-lg"></span>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        backgroundColor: 'rgba(0,0,0,0.5)',
        zIndex: 1500,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center'
      }}>
        <div style={{ backgroundColor: 'white', padding: '20px', borderRadius: '8px' }}>
          <h2>Error</h2>
          <p>{error}</p>
          <button onClick={onClose} className="btn btn-ghost">Close</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      backgroundColor: 'rgba(0,0,0,0.5)',
      zIndex: 1500,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <div style={{
        backgroundColor: 'white',
        padding: '20px',
        borderRadius: '8px',
        maxWidth: '800px',
        width: '90%',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        <h2>Update Item</h2>

        {/* Drink Action */}
        <div className="mb-4 p-4 border rounded-lg">
          <h3 className="font-bold mb-2">Drink Action</h3>
          <div className="flex gap-4">
            <label className="flex items-center">
              <input type="radio" checked={drinkAction === 'update'} onChange={() => setDrinkAction('update')} />
              <span className="ml-2">Update existing drink</span>
            </label>
            <label className="flex items-center">
              <input type="radio" checked={drinkAction === 'create'} onChange={() => setDrinkAction('create')} />
              <span className="ml-2">Save existing drink and create new</span>
            </label>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

            {/* Basic Information Card */}
            <div className="card bg-base-100 shadow">
              <details open>
                <summary>Basic Information</summary>
                <div className="card-body">
                  <MultilingualField fieldName="title" values={formData} onChange={handleFieldChange} />
                  <MultilingualField fieldName="subtitle" values={formData} onChange={handleFieldChange} />

                  {SIMPLE_FIELDS.map(field => (
                    <SimpleField
                      key={field.name}
                      name={field.name}
                      label={field.label}
                      type={field.type}
                      value={formData[field.name] || ''}
                      onChange={handleFieldChange}
                      step={field.step}
                      min={field.min}
                      max={field.max}
                    />
                  ))}

                  <div>
                    <label className="label"><span className="label-text">File</span></label>
                    <input
                      type="file"
                      onChange={e => handleFileChange((e.target as HTMLInputElement).files?.[0] || null)}
                      className="file-input file-input-bordered w-full"
                      accept="image/*"
                    />
                  </div>

                  {formData.image_path && !formData.file && (
                    <div>
                      <label className="label"><span className="label-text">Current Image</span></label>
                      <ItemImage image_id={formData.image_id} size="medium" />
                    </div>
                  )}

                  {formData.file && (
                    <div>
                      <label className="label"><span className="label-text">Selected Image Preview</span></label>
                      <img src={URL.createObjectURL(formData.file)} alt="Preview" className="max-w-xs max-h-48 object-contain border rounded" />
                    </div>
                  )}
                </div>
              </details>
            </div>

            {/* Category Card */}
            <div className="card bg-base-100 shadow">
              <details open>
                <summary>Category and Location</summary>
                <div className="card-body">
                  <SelectField
                    name="subcategory_id"
                    label="Subcategory"
                    value={formData.subcategory_id}
                    options={handbooks.subcategories}
                    onChange={handleFieldChange}
                    required
                  />
                  <SelectField
                    name="source_id"
                    label="Source"
                    value={formData.source_id}
                    options={handbooks.source}
                    onChange={handleFieldChange}
                  />
                  <SelectField
                    name="site_id"
                    label="Site"
                    value={formData.site_id}
                    options={handbooks.sites}
                    onChange={handleFieldChange}
                    required
                  />
                </div>
              </details>
            </div>

            {/* Description */}
            <MultilingualField fieldName="description" values={formData} onChange={handleFieldChange} />

            {/* Recommendation */}
            <MultilingualField fieldName="recommendation" values={formData} onChange={handleFieldChange} />

            {/* Made Of */}
            <MultilingualField fieldName="madeof" values={formData} onChange={handleFieldChange} />

            {/* Varietals */}
            <div className="card bg-base-100 shadow">
              <CheckboxGroup
                title="Varietals"
                items={handbooks.varietals}
                selectedIds={formData.varietals.map(v => v.split(':')[0])}
                onToggle={handleCheckboxToggle('varietals')}
                renderExtra={(id, isChecked) => isChecked && (
                  <input
                    type="number"
                    placeholder="%"
                    className="input input-bordered w-20 ml-2"
                    value={formData.varietals.find(v => v.startsWith(`${id}:`))?.split(':')[1] || '100'}
                    onInput={e => handleVarietalPercentage(id, (e.target as HTMLInputElement).value)}
                  />
                )}
              />
            </div>

            {/* Foods */}
            <div className="card bg-base-100 shadow">
              <CheckboxGroup
                title="Foods"
                items={handbooks.foods}
                selectedIds={formData.foods}
                onToggle={handleCheckboxToggle('foods')}
              />
            </div>
          </div>

          {/* Buttons */}
          <div className="flex justify-end gap-4 mt-6">
            <button type="button" onClick={onClose} className="btn btn-ghost" disabled={loading}>
              Cancel
            </button>
            <button type="submit" className={`btn btn-primary ${loading ? 'loading' : ''}`} disabled={loading}>
              {loading ? 'Updating...' : 'Update Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};