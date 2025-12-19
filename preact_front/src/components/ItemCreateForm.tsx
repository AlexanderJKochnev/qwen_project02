// src/components/ItemCreateForm.tsx
import { h, useState, useEffect } from 'preact/hooks';
import { apiClient } from '../lib/apiClient';
import { useLanguage } from '../contexts/LanguageContext';

interface ItemCreateFormProps {
  onClose: () => void;
  onCreated: () => void;
}

export const ItemCreateForm = ({ onClose, onCreated }: ItemCreateFormProps) => {
  const [formData, setFormData] = useState({
    title: '',
    title_ru: '',
    title_fr: '',
    subtitle: '',
    subtitle_ru: '',
    subtitle_fr: '',
    subcategory_id: '',
    sweetness_id: '',
    subregion_id: '',
    alc: '',
    sugar: '',
    age: '',
    description: '',
    description_ru: '',
    description_fr: '',
    recommendation: '',
    recommendation_ru: '',
    recommendation_fr: '',
    madeof: '',
    madeof_ru: '',
    madeof_fr: '',
    vol: '',
    price: '',
    varietals: [] as string[],
    foods: [] as string[],
    file: null as File | null
  });
  
  const [loading, setLoading] = useState(false);
  const [handbooks, setHandbooks] = useState({
    subcategories: [],
    sweetness: [],
    subregions: [],
    varietals: [],
    foods: []
  });
  
  const { language } = useLanguage();

  // Load handbook data
  useEffect(() => {
    const loadHandbooks = async () => {
      try {
        const [
          subcategories,
          sweetness,
          subregions,
          varietals,
          foods
        ] = await Promise.all([
          apiClient<any[]>(`/handbooks/subcategories/${language}`),
          apiClient<any[]>(`/handbooks/sweetness/${language}`),
          apiClient<any[]>(`/handbooks/subregions/${language}`),
          apiClient<any[]>(`/handbooks/varietals/all`),
          apiClient<any[]>(`/handbooks/foods/all`)
        ]);
        
        setHandbooks({
          subcategories,
          sweetness,
          subregions,
          varietals,
          foods
        });
      } catch (err) {
        console.error('Failed to load handbook data', err);
      }
    };
    
    loadHandbooks();
  }, [language]);

  const handleChange = (e: Event) => {
    const target = e.target as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
    const { name, value, type } = target;

    if (type === 'file') {
      const fileInput = target as HTMLInputElement;
      if (fileInput.files && fileInput.files[0]) {
        setFormData(prev => ({
          ...prev,
          file: fileInput.files[0]
        }));
      }
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setLoading(true);

    try {
      // Create form data for multipart request
      const multipartFormData = new FormData();
      
      // Add JSON string of form data
      const dataToSend = {
        ...formData,
        alc: formData.alc ? parseFloat(formData.alc) : null,
        sugar: formData.sugar ? parseFloat(formData.sugar) : null,
        vol: formData.vol ? parseFloat(formData.vol) : null,
        price: formData.price ? parseFloat(formData.price) : null,
        subcategory_id: parseInt(formData.subcategory_id),
        subregion_id: parseInt(formData.subregion_id),
        sweetness_id: formData.sweetness_id ? parseInt(formData.sweetness_id) : null,
        varietals: formData.varietals.map(v => {
          // Parse the "id:percentage" format and return in required format {id: id}
          const [id, percentage] = v.split(':');
          return { id: parseInt(id) };
        }).filter(v => !isNaN(v.id)),
        foods: formData.foods.map(f => {
          const id = parseInt(f);
          return isNaN(id) ? null : { id };
        }).filter((f): f is { id: number } => f !== null)
      };
      
      multipartFormData.append('data', JSON.stringify(dataToSend));
      
      // Add file if exists
      if (formData.file) {
        multipartFormData.append('file', formData.file);
      }

      await apiClient('/items/create_item_drink', {
        method: 'POST',
        body: multipartFormData,
        // Don't set Content-Type header, let browser set it with boundary
      }, false); // Don't include language for multipart form data
      
      onCreated();
      onClose();
    } catch (error) {
      console.error('Error creating item:', error);
      alert(`Error creating item: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

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
        <h2>Create New Item</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Basic Information */}
            <div className="card bg-base-100 shadow">
              <div className="card-body">
                <h3 className="card-title">Basic Information</h3>
                
                <div>
                  <label className="label">
                    <span className="label-text">Title *</span>
                  </label>
                  <input
                    type="text"
                    name="title"
                    value={formData.title}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    required
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Title (RU)</span>
                  </label>
                  <input
                    type="text"
                    name="title_ru"
                    value={formData.title_ru}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Title (FR)</span>
                  </label>
                  <input
                    type="text"
                    name="title_fr"
                    value={formData.title_fr}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Subtitle</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle"
                    value={formData.subtitle}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Subtitle (RU)</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle_ru"
                    value={formData.subtitle_ru}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Subtitle (FR)</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle_fr"
                    value={formData.subtitle_fr}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Volume</span>
                  </label>
                  <input
                    type="number"
                    name="vol"
                    value={formData.vol}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    step="0.01"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Price</span>
                  </label>
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    step="0.01"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">File</span>
                  </label>
                  <input
                    type="file"
                    name="file"
                    onChange={handleChange as any}
                    className="file-input file-input-bordered w-full"
                    accept="image/*"
                  />
                </div>
              </div>
            </div>
            
            {/* Category and Location */}
            <div className="card bg-base-100 shadow">
              <div className="card-body">
                <h3 className="card-title">Category and Location</h3>
                
                <div>
                  <label className="label">
                    <span className="label-text">Subcategory *</span>
                  </label>
                  <select
                    name="subcategory_id"
                    value={formData.subcategory_id}
                    onChange={handleChange as any}
                    className="select select-bordered w-full"
                    required
                  >
                    <option value="">Select a subcategory</option>
                    {handbooks.subcategories.map(subcategory => (
                      <option key={subcategory.id} value={subcategory.id}>
                        {subcategory.name || subcategory.name_en || subcategory.name_ru || subcategory.name_fr}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Sweetness</span>
                  </label>
                  <select
                    name="sweetness_id"
                    value={formData.sweetness_id}
                    onChange={handleChange as any}
                    className="select select-bordered w-full"
                  >
                    <option value="">Select sweetness</option>
                    {handbooks.sweetness.map(sweet => (
                      <option key={sweet.id} value={sweet.id}>
                        {sweet.name || sweet.name_en || sweet.name_ru || sweet.name_fr}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Subregion *</span>
                  </label>
                  <select
                    name="subregion_id"
                    value={formData.subregion_id}
                    onChange={handleChange as any}
                    className="select select-bordered w-full"
                    required
                  >
                    <option value="">Select a subregion</option>
                    {handbooks.subregions.map(subregion => (
                      <option key={subregion.id} value={subregion.id}>
                        {subregion.name || subregion.name_en || subregion.name_ru || subregion.name_fr}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Alcohol (%)</span>
                  </label>
                  <input
                    type="number"
                    name="alc"
                    value={formData.alc}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    step="0.01"
                    min="0"
                    max="100"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Sugar (%)</span>
                  </label>
                  <input
                    type="number"
                    name="sugar"
                    value={formData.sugar}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    step="0.01"
                    min="0"
                    max="100"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Age</span>
                  </label>
                  <input
                    type="text"
                    name="age"
                    value={formData.age}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
              </div>
            </div>
            
            {/* Descriptions */}
            <div className="card bg-base-100 shadow">
              <div className="card-body">
                <h3 className="card-title">Descriptions</h3>
                
                <div>
                  <label className="label">
                    <span className="label-text">Description</span>
                  </label>
                  <textarea
                    name="description"
                    value={formData.description}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Description (RU)</span>
                  </label>
                  <textarea
                    name="description_ru"
                    value={formData.description_ru}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Description (FR)</span>
                  </label>
                  <textarea
                    name="description_fr"
                    value={formData.description_fr}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
              </div>
            </div>
            
            {/* Recommendations and Made Of */}
            <div className="card bg-base-100 shadow">
              <div className="card-body">
                <h3 className="card-title">Recommendations and Made Of</h3>
                
                <div>
                  <label className="label">
                    <span className="label-text">Recommendation</span>
                  </label>
                  <textarea
                    name="recommendation"
                    value={formData.recommendation}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Recommendation (RU)</span>
                  </label>
                  <textarea
                    name="recommendation_ru"
                    value={formData.recommendation_ru}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Recommendation (FR)</span>
                  </label>
                  <textarea
                    name="recommendation_fr"
                    value={formData.recommendation_fr}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Made Of</span>
                  </label>
                  <textarea
                    name="madeof"
                    value={formData.madeof}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Made Of (RU)</span>
                  </label>
                  <textarea
                    name="madeof_ru"
                    value={formData.madeof_ru}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Made Of (FR)</span>
                  </label>
                  <textarea
                    name="madeof_fr"
                    value={formData.madeof_fr}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
              </div>
            </div>
            
            {/* Varietals and Foods */}
            <div className="card bg-base-100 shadow">
              <div className="card-body">
                <h3 className="card-title">Varietals and Foods</h3>
                
                <div>
                  <label className="label">
                    <span className="label-text">Varietals</span>
                  </label>
                  <div className="border rounded-lg p-2 max-h-40 overflow-y-auto">
                    {handbooks.varietals.map((varietal, index) => (
                      <div key={varietal.id} className="flex items-center mb-2">
                        <input
                          type="checkbox"
                          id={`varietal-${varietal.id}`}
                          checked={formData.varietals.some(v => v.startsWith(`${varietal.id}:`))}
                          onChange={(e) => {
                            const isChecked = (e.target as HTMLInputElement).checked;
                            let newVarietals = [...formData.varietals];
                            
                            if (isChecked) {
                              // Add with default 100% if not already present
                              if (!newVarietals.some(v => v.startsWith(`${varietal.id}:`))) {
                                newVarietals.push(`${varietal.id}:100`);
                              }
                            } else {
                              // Remove the varietal
                              newVarietals = newVarietals.filter(v => !v.startsWith(`${varietal.id}:`));
                            }
                            
                            setFormData(prev => ({
                              ...prev,
                              varietals: newVarietals
                            }));
                          }}
                          className="mr-2"
                        />
                        <label htmlFor={`varietal-${varietal.id}`} className="flex-1 cursor-pointer">
                          {varietal.name || varietal.name_en || varietal.name_ru || varietal.name_fr}
                        </label>
                        {formData.varietals.some(v => v.startsWith(`${varietal.id}:`)) && (
                          <div className="ml-2">
                            <input
                              type="number"
                              min="0"
                              max="100"
                              step="0.1"
                              placeholder="%" 
                              value={
                                formData.varietals.find(v => v.startsWith(`${varietal.id}:`))
                                  ? formData.varietals.find(v => v.startsWith(`${varietal.id}:`)).split(':')[1]
                                  : '100'
                              }
                              onChange={(e) => {
                                const percentage = (e.target as HTMLInputElement).value;
                                const newVarietals = formData.varietals.map(v => 
                                  v.startsWith(`${varietal.id}:`) ? `${varietal.id}:${percentage}` : v
                                );
                                
                                setFormData(prev => ({
                                  ...prev,
                                  varietals: newVarietals
                                }));
                              }}
                              className="input input-bordered w-20"
                            />
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Foods</span>
                  </label>
                  <div className="border rounded-lg p-2 max-h-40 overflow-y-auto">
                    {handbooks.foods.map(food => (
                      <div key={food.id} className="flex items-center mb-2">
                        <input
                          type="checkbox"
                          id={`food-${food.id}`}
                          checked={formData.foods.includes(food.id.toString())}
                          onChange={(e) => {
                            const isChecked = (e.target as HTMLInputElement).checked;
                            let newFoods = [...formData.foods];
                            
                            if (isChecked) {
                              if (!newFoods.includes(food.id.toString())) {
                                newFoods.push(food.id.toString());
                              }
                            } else {
                              newFoods = newFoods.filter(f => f !== food.id.toString());
                            }
                            
                            setFormData(prev => ({
                              ...prev,
                              foods: newFoods
                            }));
                          }}
                          className="mr-2"
                        />
                        <label htmlFor={`food-${food.id}`} className="cursor-pointer">
                          {food.name || food.name_en || food.name_ru || food.name_fr}
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          <div className="flex justify-end gap-4 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-ghost"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className={`btn btn-primary ${loading ? 'loading' : ''}`}
              disabled={loading}
            >
              {loading ? 'Creating...' : 'Create Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};