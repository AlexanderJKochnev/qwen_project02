// src/pages/ItemUpdateForm.tsx
import { h, useState, useEffect } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { apiClient } from '../lib/apiClient';
import { useLanguage } from '../contexts/LanguageContext';
import { IMAGE_BASE_URL } from '../config/api';

interface ItemUpdateFormProps {
  onClose: () => void;
  onUpdated?: () => void;
}

export const ItemUpdateForm = ({ onClose, onUpdated }: ItemUpdateFormProps) => {
  const { url } = useLocation();
  // Extract ID from URL path - expecting format like /items/edit/123
  const pathParts = url.split('/');
  const idParam = pathParts[pathParts.length - 1]; // Get the last part of the path
  const id = parseInt(idParam);

  // Check if ID is valid
  if (isNaN(id)) {
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
          <h2>Invalid Item ID: {idParam}</h2>
          <button
            onClick={onClose}
            className="btn btn-ghost"
          >
            Close
          </button>
        </div>
      </div>
    );
  }
  
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
    varietals: [] as string[], // Format: "id:percentage"
    foods: [] as string[],
    file: null as File | null,
    drink_id: 0,
    image_id: '',
    image_path: '',
    count: 0,
    id: 0
  });

  const [drinkAction, setDrinkAction] = useState<'update' | 'create'>('update');
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);
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

        // Sort each handbook alphabetically by the visible field
        const getVisibleName = (item: any) => {
          return item.name || item.name_en || item.name_ru || item.name_fr || '';
        };

        const sortedSubcategories = [...subcategories].sort((a, b) =>
          getVisibleName(a).localeCompare(getVisibleName(b))
        );
        const sortedSweetness = [...sweetness].sort((a, b) =>
          getVisibleName(a).localeCompare(getVisibleName(b))
        );
        const sortedSubregions = [...subregions].sort((a, b) =>
          getVisibleName(a).localeCompare(getVisibleName(b))
        );
        const sortedVarietals = [...varietals].sort((a, b) =>
          getVisibleName(a).localeCompare(getVisibleName(b))
        );
        const sortedFoods = [...foods].sort((a, b) =>
          getVisibleName(a).localeCompare(getVisibleName(b))
        );

        setHandbooks({
          subcategories: sortedSubcategories,
          sweetness: sortedSweetness,
          subregions: sortedSubregions,
          varietals: sortedVarietals,
          foods: sortedFoods
        });
      } catch (err) {
        console.error('Failed to load handbook data', err);
        setError('Failed to load handbook data');
      }
    };

    loadHandbooks();
  }, [language]);

  // Load initial data for update
  useEffect(() => {
    const loadItemData = async () => {
      try {
        setLoadingData(true);
        const data = await apiClient<any>(`/preact/${id}`, {
          method: 'GET'
        });
        
        // Create arrays of checked items from the loaded data
        const checkedVarietals = data.varietals || [];
        const checkedFoodIds = new Set((data.foods || []).map(f => f.id.toString()));
        
        // Prepare varietals array with checked items first, then unchecked (alphabetically)
        const checkedVarietalsArray = checkedVarietals.map(v => `${v.id}:${v.percentage}`);
        
        const uncheckedVarietals = handbooks.varietals.filter(v => 
          !checkedVarietals.some(cv => cv.id === v.id)
        ).map(v => `${v.id}:100`); // Default percentage for unchecked items
        
        // Combine: checked first, then unchecked sorted alphabetically by name
        const allVarietalsWithNames = [
          ...checkedVarietals.map(v => ({ id: v.id, percentage: v.percentage, name: handbooks.varietals.find(hv => hv.id === v.id)?.name || v.name_en || v.name_ru || v.name_fr || '' })),
          ...uncheckedVarietals.map(v => {
            const [varId] = v.split(':');
            const varIntId = parseInt(varId);
            const varietal = handbooks.varietals.find(hv => hv.id === varIntId);
            return { 
              id: varIntId, 
              percentage: 100, 
              name: varietal?.name || varietal?.name_en || varietal?.name_ru || varietal?.name_fr || '' 
            };
          })
        ].sort((a, b) => {
          // First priority: checked items first
          const aIsChecked = checkedVarietals.some(cv => cv.id === a.id);
          const bIsChecked = checkedVarietals.some(cv => cv.id === b.id);
          
          if (aIsChecked && !bIsChecked) return -1;
          if (!aIsChecked && bIsChecked) return 1;
          
          // Second priority: alphabetical by name
          return a.name.localeCompare(b.name);
        });
        
        const sortedVarietals = allVarietalsWithNames.map(v => `${v.id}:${v.percentage}`);
        
        // Prepare foods array with checked items first, then unchecked (alphabetically)
        const checkedFoodsArray = (data.foods || []).map(f => f.id.toString());
        
        const uncheckedFoods = handbooks.foods.filter(f => 
          !checkedFoodIds.has(f.id.toString())
        );
        
        // Combine: checked first, then unchecked sorted alphabetically by name
        const allFoodsWithNames = [
          ...(data.foods || []).map(f => ({ 
            id: f.id, 
            name: handbooks.foods.find(hf => hf.id === f.id)?.name || f.name_en || f.name_ru || f.name_fr || ''
          })),
          ...uncheckedFoods.map(f => ({ 
            id: f.id, 
            name: f.name || f.name_en || f.name_ru || f.name_fr || '' 
          }))
        ].sort((a, b) => {
          // First priority: checked items first
          const aIsChecked = checkedFoodIds.has(a.id.toString());
          const bIsChecked = checkedFoodIds.has(b.id.toString());
          
          if (aIsChecked && !bIsChecked) return -1;
          if (!aIsChecked && bIsChecked) return 1;
          
          // Second priority: alphabetical by name
          return a.name.localeCompare(b.name);
        });
        
        const sortedFoods = allFoodsWithNames.map(f => f.id.toString());

        setFormData({
          title: data.title || '',
          title_ru: data.title_ru || '',
          title_fr: data.title_fr || null || '',
          subtitle: data.subtitle || '',
          subtitle_ru: data.subtitle_ru || '',
          subtitle_fr: data.subtitle_fr || null || '',
          subcategory_id: data.subcategory_id ? data.subcategory_id.toString() : '',
          sweetness_id: data.sweetness_id ? data.sweetness_id.toString() : '',
          subregion_id: data.subregion_id ? data.subregion_id.toString() : '',
          alc: data.alc ? data.alc.toString() : '',
          sugar: data.sugar ? data.sugar.toString() : '',
          age: data.age || '',
          description: data.description || '',
          description_ru: data.description_ru || '',
          description_fr: data.description_fr || null || '',
          recommendation: data.recommendation || '',
          recommendation_ru: data.recommendation_ru || '',
          recommendation_fr: data.recommendation_fr || null || '',
          madeof: data.madeof || '',
          madeof_ru: data.madeof_ru || '',
          madeof_fr: data.madeof_fr || null || '',
          vol: data.vol ? data.vol.toString() : '',
          price: data.price ? data.price.toString() : '',
          varietals: sortedVarietals,
          foods: sortedFoods,
          file: null,
          drink_id: data.drink_id || 0,
          image_id: data.image_id || '',
          image_path: data.image_path || '',
          count: data.count || 0,
          id: data.id || 0
        });
      } catch (err) {
        console.error('Failed to load item data', err);
        setError('Failed to load item data: ' + err.message);
      } finally {
        setLoadingData(false);
      }
    };

    if (handbooks.varietals.length > 0 && handbooks.foods.length > 0) {
      loadItemData();
    }
  }, [id, handbooks]);

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
    } else if (type === 'checkbox') {
      const checkbox = target as HTMLInputElement;
      const { name } = checkbox;
      
      if (name.startsWith('varietal-')) {
        const varietalId = name.split('-')[1];
        const isChecked = checkbox.checked;
        
        let newVarietals = [...formData.varietals];
        
        if (isChecked) {
          // Add with default 100% if not already present
          if (!newVarietals.some(v => v.startsWith(`${varietalId}:`))) {
            newVarietals.push(`${varietalId}:100`);
          }
        } else {
          // Remove the varietal
          newVarietals = newVarietals.filter(v => !v.startsWith(`${varietalId}:`));
        }
        
        setFormData(prev => ({
          ...prev,
          varietals: newVarietals
        }));
      } else if (name.startsWith('food-')) {
        const foodId = name.split('-')[1];
        const isChecked = checkbox.checked;
        
        let newFoods = [...formData.foods];
        
        if (isChecked) {
          if (!newFoods.includes(foodId)) {
            newFoods.push(foodId);
          }
        } else {
          newFoods = newFoods.filter(f => f !== foodId);
        }
        
        setFormData(prev => ({
          ...prev,
          foods: newFoods
        }));
      }
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleVarietalPercentageChange = (varietalId: string, percentage: string) => {
    const newVarietals = formData.varietals.map(v =>
      v.startsWith(`${varietalId}:`) ? `${varietalId}:${percentage}` : v
    );
    
    setFormData(prev => ({
      ...prev,
      varietals: newVarietals
    }));
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
          // Parse the "id:percentage" format and return in required format {id: id, percentage: percentage}
          const [id, percentage] = v.split(':');
          return { id: parseInt(id), percentage: parseFloat(percentage) };
        }).filter(v => !isNaN(v.id) && !isNaN(v.percentage)),
        foods: formData.foods.map(f => {
          const id = parseInt(f);
          return isNaN(id) ? null : { id };
        }).filter((f): f is { id: number } => f !== null),
        drink_action: drinkAction, // Add the drink action
        drink_id: formData.drink_id // Include drink_id for update
      };

      // Only include image_path and image_id if no file is being uploaded
      if (!formData.file) {
        delete dataToSend.image_path;
        delete dataToSend.image_id;
      }

      multipartFormData.append('data', JSON.stringify(dataToSend));

      // Add file if exists
      if (formData.file) {
        multipartFormData.append('file', formData.file);
      }

      await apiClient(`/items/update_item_drink/${id}`, {
        method: 'POST',
        body: multipartFormData,
        // Don't set Content-Type header, let browser set it with boundary
      }, false); // Don't include language for multipart form data

      if (onUpdated) {
        onUpdated();
      }
      onClose();
    } catch (error) {
      console.error('Error updating item:', error);
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
        <div style={{
          backgroundColor: 'white',
          padding: '20px',
          borderRadius: '8px',
          maxWidth: '800px',
          width: '90%',
          maxHeight: '90vh',
          overflowY: 'auto'
        }}>
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
        <div style={{
          backgroundColor: 'white',
          padding: '20px',
          borderRadius: '8px',
          maxWidth: '800px',
          width: '90%',
          maxHeight: '90vh',
          overflowY: 'auto'
        }}>
          <h2>Error</h2>
          <p>{error}</p>
          <button
            onClick={onClose}
            className="btn btn-ghost"
          >
            Close
          </button>
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

        {/* Drink Action Radio Buttons */}
        <div className="mb-4 p-4 border rounded-lg">
          <h3 className="font-bold mb-2">Drink Action</h3>
          <div className="flex items-center space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="drinkAction"
                checked={drinkAction === 'update'}
                onChange={() => setDrinkAction('update')}
                className="mr-2"
              />
              <span>Update existing drink</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="drinkAction"
                checked={drinkAction === 'create'}
                onChange={() => setDrinkAction('create')}
                className="mr-2"
              />
              <span>Save existing drink and create new</span>
            </label>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Basic Information */}
            <div className="card bg-base-100 shadow">
            <details>
              <summary>Basic Information</summary>
              <div className="card-body">

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

                {/* Display current image if available */}
                {formData.image_path && !formData.file && (
                  <div>
                    <label className="label">
                      <span className="label-text">Current Image</span>
                    </label>
                    <span className="half-life">
                    <img
                      src={`${IMAGE_BASE_URL}/mongodb/thumbnails/${formData.image_id}`}
                      alt="Current item" 
                      className="max-w-xs max-h-48 object-contain border rounded"
                    />
                    </span>
                  </div>
                )}

                {/* Display selected file preview */}
                {formData.file && (
                  <div>
                    <label className="label">
                      <span className="label-text">Selected Image Preview</span>
                    </label>
                    <span className="half-life">
                    <img
                      src={URL.createObjectURL(formData.file)} 
                      alt="Selected item" 
                      className="max-w-xs max-h-48 object-contain border rounded"
                    />
                    </span>
                  </div>
                )}
              </div>
            </details>
            </div>

            {/* Category and Location */}
            <div className="card bg-base-100 shadow">
            <details>
              <summary>Category and Location</summary>
              <div className="card-body">
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
            </details>
            </div>

            {/* Descriptions */}
            <div className="card bg-base-100 shadow">
            <details>
              <summary>Descriptions</summary>
              <div className="card-body">
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
            </details>
            </div>

            {/* Recommendations and Made Of */}
            <div className="card bg-base-100 shadow">
            <details>
            <summary>Recommendations and Made Of</summary>
              <div className="card-body">
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
            </details>
            </div>

            {/* Varietals and Foods */}
            <div className="card bg-base-100 shadow">
              <div className="card-body">
              <details> <summary>Varietals</summary>
                <div className="card-body">
                  <div className="border rounded-lg p-2 max-h-40 overflow-y-auto">
                    {formData.varietals.map((varietalStr, index) => {
                      const [varietalId, percentage] = varietalStr.split(':');
                      const varietal = handbooks.varietals.find(v => v.id === parseInt(varietalId));
                      
                      if (!varietal) return null;
                      
                      return (
                        <div key={varietal.id} className="flex items-center mb-2">
                          <input
                            type="checkbox"
                            id={`varietal-${varietal.id}`}
                            name={`varietal-${varietal.id}`}
                            checked={formData.varietals.some(v => v.startsWith(`${varietal.id}:`))}
                            onChange={handleChange as any}
                            className="mr-2"
                          />
                          <label htmlFor={`varietal-${varietal.id}`} className="flex-1 cursor-pointer">
                            {varietal.name || varietal.name_en || varietal.name_ru || varietal.name_fr}
                          </label>
                          <div className="ml-2">
                            <input
                              type="number"
                              min="0"
                              max="100"
                              step="0.1"
                              placeholder="%"
                              value={percentage}
                              onChange={(e) => handleVarietalPercentageChange(varietal.id.toString(), (e.target as HTMLInputElement).value)}
                              className="input input-bordered w-20"
                            />
                          </div>
                        </div>
                      );
                    })}
                    {/* Render unchecked varietals after the checked ones */}
                    {handbooks.varietals
                      .filter(v => !formData.varietals.some(fv => fv.startsWith(`${v.id}:`)))
                      .map(varietal => {
                        return (
                          <div key={varietal.id} className="flex items-center mb-2">
                            <input
                              type="checkbox"
                              id={`varietal-${varietal.id}`}
                              name={`varietal-${varietal.id}`}
                              checked={false}
                              onChange={handleChange as any}
                              className="mr-2"
                            />
                            <label htmlFor={`varietal-${varietal.id}`} className="flex-1 cursor-pointer">
                              {varietal.name || varietal.name_en || varietal.name_ru || varietal.name_fr}
                            </label>
                          </div>
                        );
                      })}
                  </div>
                </div>
                </details>
              </div>
              </div>
            <div className="card bg-base-100 shadow">
              <details><summary> Foods </summary>
                  <div className="border rounded-lg p-2 max-h-40 overflow-y-auto">
                    {formData.foods.map((foodId) => {
                      const food = handbooks.foods.find(f => f.id === parseInt(foodId));
                      
                      if (!food) return null;
                      
                      return (
                        <div key={food.id} className="flex items-center mb-2">
                          <input
                            type="checkbox"
                            id={`food-${food.id}`}
                            name={`food-${food.id}`}
                            checked={formData.foods.includes(food.id.toString())}
                            onChange={handleChange as any}
                            className="mr-2"
                          />
                          <label htmlFor={`food-${food.id}`} className="cursor-pointer">
                            {food.name || food.name_en || food.name_ru || food.name_fr}
                          </label>
                        </div>
                      );
                    })}
                    {/* Render unchecked foods after the checked ones */}
                    {handbooks.foods
                      .filter(f => !formData.foods.includes(f.id.toString()))
                      .sort((a, b) => {
                        // Sort alphabetically by language name
                        const aName = a.name || a.name_en || a.name_ru || a.name_fr || "";
                        const bName = b.name || b.name_en || b.name_ru || b.name_fr || "";
                        return aName.localeCompare(bName);
                      })
                      .map(food => {
                        return (
                          <div key={food.id} className="flex items-center mb-2">
                            <input
                              type="checkbox"
                              id={`food-${food.id}`}
                              name={`food-${food.id}`}
                              checked={false}
                              onChange={handleChange as any}
                              className="mr-2"
                            />
                            <label htmlFor={`food-${food.id}`} className="cursor-pointer">
                              {food.name || food.name_en || food.name_ru || food.name_fr}
                            </label>
                          </div>
                        );
                      })}
                  </div>
                  </details>
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
              {loading ? 'Updating...' : 'Update Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};