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
    title_es: '',
    title_it: '',
    title_de: '',
    title_zh: '',
    subtitle: '',
    subtitle_ru: '',
    subtitle_fr: '',
    subtitle_es: '',
    subtitle_it: '',
    subtitle_de: '',
    subtitle_zh: '',
    subcategory_id: '',
    sweetness_id: '',
    subregion_id: '',
    alc: '',
    sugar: '',
    age: '',
    description: '',
    description_ru: '',
    description_fr: '',
    description_es: '',
    description_it: '',
    description_de: '',
    description_zh: '',
    recommendation: '',
    recommendation_ru: '',
    recommendation_fr: '',
    recommendation_es: '',
    recommendation_it: '',
    recommendation_de: '',
    recommendation_zh: '',
    madeof: '',
    madeof_ru: '',
    madeof_fr: '',
    madeof_es: '',
    madeof_it: '',
    madeof_de: '',
    madeof_zh: '',
    vol: '',
    price: '',
    varietals: [] as string[], // Format: "id:percentage"
    foods: [] as string[],
    file: null as File | null,
    drink_id: 0,
    id: 0,
    image_id: '',
    image_path: '',
    count: 0
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
          return item.name || item.name_en || item.name_ru || item.name_fr || item.name_es || item.name_it || item.name_de || item.name_zh || '';
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
        
        console.log('Item data loaded for ID:', id, data);
        console.log('data.varietals:', data.varietals);
        // Create arrays of checked items from the loaded data
        const checkedVarietals = data.varietals || [];
        const checkedFoodIds = new Set((data.foods || []).map(f => f.id.toString()));
        
        // Only store the checked varietals in formData (with their percentages)
        const sortedVarietals = [...checkedVarietals]
          .sort((a, b) => {
            // Sort checked items alphabetically by name
            const aName = handbooks.varietals.find(hv => hv.id === a.id)?.name || a.name_en || a.name_ru || a.name_fr || item.name_es || item.name_it || item.name_de || item.name_zh || '';
            const bName = handbooks.varietals.find(hv => hv.id === b.id)?.name || b.name_en || b.name_ru || b.name_fr || item.name_es || item.name_it || item.name_de || item.name_zh || '';
            return aName.localeCompare(bName);
          })
          .map(v => `${v.id}:${v.percentage}`);
        
        // Only store the checked foods in formData
        const sortedFoods = [...(data.foods || [])]
          .sort((a, b) => {
            // Sort checked items alphabetically by name
            const aName = handbooks.foods.find(hf => hf.id === a.id)?.name || a.name_en || a.name_ru || a.name_fr || item.name_es || item.name_it || item.name_de || item.name_zh || '';
            const bName = handbooks.foods.find(hf => hf.id === b.id)?.name || b.name_en || b.name_ru || b.name_fr || item.name_es || item.name_it || item.name_de || item.name_zh || '';
            return aName.localeCompare(bName);
          })
          .map(f => f.id.toString());

        setFormData({
          title: data.title || '',
          title_ru: data.title_ru || '',
          title_fr: data.title_fr || null || '',
          title_es: data.title_es || null || '',
          title_it: data.title_it || null || '',
          title_de: data.title_de || null || '',
          title_zh: data.title_zh || null || '',
          subtitle: data.subtitle || '',
          subtitle_ru: data.subtitle_ru || '',
          subtitle_fr: data.subtitle_fr || null || '',
          subtitle_es: data.subtitle_es || null || '',
          subtitle_it: data.subtitle_it || null || '',
          subtitle_de: data.subtitle_de || null || '',
          subtitle_zh: data.subtitle_zh || null || '',
          subcategory_id: data.subcategory_id ? data.subcategory_id.toString() : '',
          sweetness_id: data.sweetness_id ? data.sweetness_id.toString() : '',
          subregion_id: data.subregion_id ? data.subregion_id.toString() : '',
          alc: data.alc ? data.alc.toString() : '',
          sugar: data.sugar ? data.sugar.toString() : '',
          age: data.age || '',
          description: data.description || '',
          description_ru: data.description_ru || '',
          description_fr: data.description_fr || null || '',
          description_es: data.description_es || null || '',
          description_it: data.description_it || null || '',
          description_de: data.description_de || null || '',
          description_zh: data.description_zh || null || '',
          recommendation: data.recommendation || '',
          recommendation_ru: data.recommendation_ru || '',
          recommendation_fr: data.recommendation_fr || null || '',
          recommendation_es: data.recommendation_es || null || '',
          recommendation_it: data.recommendation_it || null || '',
          recommendation_de: data.recommendation_de || null || '',
          recommendation_zh: data.recommendation_zh || null || '',
          madeof: data.madeof || '',
          madeof_ru: data.madeof_ru || '',
          madeof_fr: data.madeof_fr || null || '',
          madeof_es: data.madeof_es || null || '',
          madeof_it: data.madeof_it || null || '',
          madeof_de: data.madeof_de || null || '',
          madeof_zh: data.madeof_zh || null || '',
          vol: data.vol ? data.vol.toString() : '',
          price: data.price ? data.price.toString() : '',
          varietals: sortedVarietals,
          foods: sortedFoods,
          file: null,
          drink_id: data.drink_id || 0,
          image_id: data.image_id || '',
          image_path: data.image_path || '',
          count: data.count || 0,
          id: id || 0
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
  }, [id, handbooks.varietals, handbooks.foods]); // Added specific dependencies instead of whole handbooks object

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
        drink_id: formData.drink_id, // Include drink_id for update
        id: formData.id // Include Item id for update
      };

      console.log('Sending data to update:', JSON.stringify(dataToSend));

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
        method: 'PATCH',
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
                    placeholder="Title"
                    required
                  />
                </div>
                <div>
                  <label className="label">
                    <span className="label-text">Title (Russian)</span>
                  </label>
                  <input
                    type="text"
                    name="title_ru"
                    value={formData.title_ru}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Заголовок на Русском"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Title (French)</span>
                  </label>
                  <input
                    type="text"
                    name="title_fr"
                    value={formData.title_fr}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Titre en Francais"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Title (Spanish)</span>
                  </label>
                  <input
                    type="text"
                    name="title_es"
                    value={formData.title_es}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Título en español"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Title (Italian)</span>
                  </label>
                  <input
                    type="text"
                    name="title_it"
                    value={formData.title_it}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Titolo"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Title (German)</span>
                  </label>
                  <input
                    type="text"
                    name="title_de"
                    value={formData.title_de}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Titel"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Title (Chinese)</span>
                  </label>
                  <input
                    type="text"
                    name="title_zh"
                    value={formData.title_zh}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="標題"
                  />
                </div>

                {/* lang title */}
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
                    placeholder="Subtitle"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Subtitle (Russian)</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle_ru"
                    value={formData.subtitle_ru}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Наименование"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Subtitle (French)</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle_fr"
                    value={formData.subtitle_fr}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Subtitre"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Subtitle (Spanish)</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle_es"
                    value={formData.subtitle_es}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Subtítulo en español"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Subtitle (Italian)</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle_it"
                    value={formData.subtitle_it}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Sottotitolo"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Subtitle (German)</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle_de"
                    value={formData.subtitle_de}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Untertitel"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Subtitle (Chinese)</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle_zh"
                    value={formData.subtitle_zh}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="標題"
                  />
                </div>

                {/* lang subtitle */}

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
                        {subcategory.name || subcategory.name_en || subcategory.name_ru || subcategory.name_fr || subcategory.name_es || subcategory.name_it || subcategory.name_de || subcategory.name_zh}
                        {/* lang subcategory*/}
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
                        {sweet.name || sweet.name_en || sweet.name_ru || sweet.name_fr || sweet.name_es || sweet.name_it || sweet.name_de || sweet.name_zh}
                        {/* lang sweet */}
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
                        {subregion.name || subregion.name_en || subregion.name_ru || subregion.name_fr || subregion.name_es || subregion.name_it || subregion.name_de || subregion.name_zh}
                        {/* lang subregion*/}
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
                    placeholder="Description"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Description (Russian)</span>
                  </label>
                  <textarea
                    name="description_ru"
                    value={formData.description_ru}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Описание"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Description (French)</span>
                  </label>
                  <textarea
                    name="description_fr"
                    value={formData.description_fr}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Description"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Description (Spain)</span>
                  </label>
                  <textarea
                    name="description_es"
                    value={formData.description_es}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Descripción en español"
                  />
                </div>

                <div>
                    <label className="label">
                      <span className="label-text">Description (Italy)</span>
                    </label>
                    <textarea
                      name="description_it"
                      value={formData.description_it}
                      onInput={handleChange}
                      className="textarea textarea-bordered w-full"
                      rows={3}
                      placeholder="Descrizione in italiano"
                    />
                </div>

                <div>
                    <label className="label">
                      <span className="label-text">Description (German)</span>
                    </label>
                    <textarea
                      name="description_de"
                      value={formData.description_de}
                      onInput={handleChange}
                      className="textarea textarea-bordered w-full"
                      rows={3}
                      placeholder="Beschreibung auf Deutsch"
                    />
                </div>

                <div>
                    <label className="label">
                      <span className="label-text">Description (Chinese)</span>
                    </label>
                    <textarea
                      name="description_zh"
                      value={formData.description_zh}
                      onInput={handleChange}
                      className="textarea textarea-bordered w-full"
                      rows={3}
                      placeholder="中文說明"
                    />
                </div>
                {/* lang description */}
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
                    placeholder="Recommendation"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Recommendation (Russian)</span>
                  </label>
                  <textarea
                    name="recommendation_ru"
                    value={formData.recommendation_ru}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Рекомендации"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Recommendation (French)</span>
                  </label>
                  <textarea
                    name="recommendation_fr"
                    value={formData.recommendation_fr}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Recommandation"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Recommendation (Spanish)</span>
                  </label>
                  <textarea
                    name="recommendation_es"
                    value={formData.recommendation_es}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Recomendación"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Recommendation (Italian)</span>
                  </label>
                  <textarea
                    name="recommendation_it"
                    value={formData.recommendation_it}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Raccomandazione"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Recommendation (German)</span>
                  </label>
                  <textarea
                    name="recommendation_de"
                    value={formData.recommendation_de}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Empfehlung"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Recommendation (Chinese)</span>
                  </label>
                  <textarea
                    name="recommendation_zh"
                    value={formData.recommendation_zh}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="推薦"
                  />
                </div>

                {/* lang recommendation */}

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
                    placeholder="Made of"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Made Of (Russian)</span>
                  </label>
                  <textarea
                    name="madeof_ru"
                    value={formData.madeof_ru}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Сделано из"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Made Of (French)</span>
                  </label>
                  <textarea
                    name="madeof_fr"
                    value={formData.madeof_fr}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Fait de"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Made Of (Spanish)</span>
                  </label>
                  <textarea
                    name="madeof_es"
                    value={formData.madeof_es}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Hecho de"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Made Of (Italian)</span>
                  </label>
                  <textarea
                    name="madeof_it"
                    value={formData.madeof_it}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Fatto di"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Made Of (German)</span>
                  </label>
                  <textarea
                    name="madeof_de"
                    value={formData.madeof_de}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="Hergestellt aus"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Made Of (Chinese)</span>
                  </label>
                  <textarea
                    name="madeof_zh"
                    value={formData.madeof_zh}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                    placeholder="製成"
                  />
                </div>

                {/* lanf madeof*/}
              </div>
            </details>
            </div>

            {/* Varietals and Foods */}
            <div className="card bg-base-100 shadow">
              <div className="card-body">
              <details> <summary>Varietals</summary>
                <div className="card-body">
                  <div className="border rounded-lg p-2 max-h-40 overflow-y-auto">
                    {/* Render all varietals with proper sorting: checked first, then alphabetical */}
                    {[...handbooks.varietals]
                      .sort((a, b) => {
                        // First priority: checked items first
                        const aIsChecked = formData.varietals.some(v => v.startsWith(`${a.id}:`));
                        const bIsChecked = formData.varietals.some(v => v.startsWith(`${b.id}:`));

                        if (aIsChecked && !bIsChecked) return -1;
                        if (!aIsChecked && bIsChecked) return 1;

                        // Second priority: alphabetical by name
                        const aName = a.name || a.name_en || a.name_ru || a.name_fr || a.name_es || a.name_it || a.name_de || a.name_zh || "";
                        const bName = b.name || b.name_en || b.name_ru || b.name_fr || b.name_es || b.name_it || b.name_de || b.name_zh || "";
                        {/* varieta l*/}
                        return aName.localeCompare(bName);
                      })
                      .map(varietal => {
                        const varietalData = formData.varietals.find(v => v.startsWith(`${varietal.id}:`));
                        const isChecked = !!varietalData;
                        const percentage = isChecked ? varietalData.split(':')[1] : '100';

                        return (
                          <div key={varietal.id} className="flex items-center mb-2">
                            <input
                              type="checkbox"
                              id={`varietal-${varietal.id}`}
                              name={`varietal-${varietal.id}`}
                              checked={isChecked}
                              onChange={handleChange as any}
                              className="mr-2"
                            />
                            <label htmlFor={`varietal-${varietal.id}`} className="flex-1 cursor-pointer">
                              {varietal.name || varietal.name_en || varietal.name_ru || varietal.name_fr || varietal.name_es || varietal.name_it || varietal.name_de || varietal.name_zh}
                              {/* lang varietal.name */}
                            </label>
                            {isChecked && (
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
                            )}
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
                    {/* Render all foods with proper sorting: checked first, then alphabetical */}
                    {[...handbooks.foods]
                      .sort((a, b) => {
                        // First priority: checked items first
                        const aIsChecked = formData.foods.includes(a.id.toString());
                        const bIsChecked = formData.foods.includes(b.id.toString());

                        if (aIsChecked && !bIsChecked) return -1;
                        if (!aIsChecked && bIsChecked) return 1;

                        // Second priority: alphabetical by name
                        const aName = a.name || a.name_en || a.name_ru || a.name_fr || a.name_es || a.name_it || a.name_de || a.name_zh || "";
                        const bName = b.name || b.name_en || b.name_ru || b.name_fr || b.name_es || b.name_it || b.name_de || b.name_zh || "";
                        {/* lang fooods */}
                        return aName.localeCompare(bName);
                      })
                      .map(food => {
                        const isChecked = formData.foods.includes(food.id.toString());

                        return (
                          <div key={food.id} className="flex items-center mb-2">
                            <input
                              type="checkbox"
                              id={`food-${food.id}`}
                              name={`food-${food.id}`}
                              checked={isChecked}
                              onChange={handleChange as any}
                              className="mr-2"
                            />
                            <label htmlFor={`food-${food.id}`} className="cursor-pointer">
                              {food.name || food.name_en || food.name_ru || food.name_fr || food.name_es || food.name_it || food.name_de || food.name_zh}
                              {/* lang food.name */}
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