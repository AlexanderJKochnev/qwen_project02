// src/pages/ItemUpdateForm.tsx
import { h, useState, useEffect } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { Link } from '../components/Link';
import { useApi } from '../hooks/useApi';
import { apiClient } from '../lib/apiClient';
import { ItemRead } from '../types/item';
import { useNotification } from '../hooks/useNotification';
import { useLanguage } from '../contexts/LanguageContext';

export const ItemUpdateForm = () => {
  const { url } = useLocation();
  // Extract ID from URL path - expecting format like /items/edit/123
  const pathParts = url.split('/');
  const idParam = pathParts[pathParts.length - 1]; // Get the last part of the path
  const id = parseInt(idParam);
  const { route } = useLocation();
  const { showNotification } = useNotification();

  // Check if ID is valid
  if (isNaN(id)) {
    return (
      <div className="alert alert-error">
        <div>
          <span>Invalid item ID: {idParam}</span>
        </div>
      </div>
    );
  }
  
  const { language } = useLanguage();
  
  const { data: viewData, loading: loadingItem, error: errorItem } = useApi<ItemRead>(
    `/items_view/detail/${language}/${id}`,
    'GET'
  );
  
  // Get the raw item data to access drink_id
  const { data: itemData } = useApi<any>(
    `/items/${id}`,
    'GET'
  );
  
  const [formData, setFormData] = useState({
    vol: 0,
    price: 0,
    count: 0,
    image_id: '',
    category: '',
    country: '',
    region: '',
    en: { title: '', subtitle: '', description: '', recommendation: '', madeof: '', alc: '', sugar: '', age: '', sparkling: false, pairing: [], varietal: [] },
    ru: { title: '', subtitle: '', description: '', recommendation: '', madeof: '', alc: '', sugar: '', age: '', sparkling: false, pairing: [], varietal: [] },
    fr: { title: '', subtitle: '', description: '', recommendation: '', madeof: '', alc: '', sugar: '', age: '', sparkling: false, pairing: [], varietal: [] }
  });
  const [loading, setLoading] = useState(false);
  const [handbooks, setHandbooks] = useState({
    categories: [],
    countries: [],
    regions: [],
    subcategories: [],
    subregions: [],
    sweetness: [],
    superfoods: [],
    foods: [],
    varietals: []
  });

  // Load handbook data
  useEffect(() => {
    const loadHandbooks = async () => {
      try {
        const [
          categories,
          countries,
          regions,
          subcategories,
          subregions,
          sweetness,
          superfoods,
          foods,
          varietals
        ] = await Promise.all([
          apiClient<any[]>('/categories/all'),
          apiClient<any[]>('/countries/all'),
          apiClient<any[]>('/regions/all'),
          apiClient<any[]>('/subcategories/all'),
          apiClient<any[]>('/subregions/all'),
          apiClient<any[]>('/sweetness/all'),
          apiClient<any[]>('/superfoods/all'),
          apiClient<any[]>('/foods/all'),
          apiClient<any[]>('/varietals/all'),
        ]);
        setHandbooks({
          categories,
          countries,
          regions,
          subcategories,
          subregions,
          sweetness,
          superfoods,
          foods,
          varietals
        });
      } catch (err) {
        console.error('Failed to load handbook data', err);
        showNotification('Failed to load handbook data', 'error');
      }
    };
    loadHandbooks();
  }, []);

  // Load initial data when item is loaded
  useEffect(() => {
    if (viewData) {
      setFormData({
        vol: viewData.vol || 0,
        price: viewData.price || 0,
        count: viewData.count || 0,
        image_id: viewData.image_id || '',
        category: viewData.category || '',
        country: viewData.country || '',
        region: viewData.region || '',
        en: {
          title: viewData.en?.title || '',
          subtitle: viewData.en?.subtitle || '',
          description: viewData.en?.description || '',
          recommendation: viewData.en?.recommendation || '',
          madeof: viewData.en?.madeof || '',
          alc: viewData.en?.alc || '',
          sugar: viewData.en?.sugar || '',
          age: viewData.en?.age || '',
          sparkling: viewData.en?.sparkling || false,
          pairing: viewData.en?.pairing || [],
          varietal: viewData.en?.varietal || []
        },
        ru: {
          title: viewData.ru?.title || '',
          subtitle: viewData.ru?.subtitle || '',
          description: viewData.ru?.description || '',
          recommendation: viewData.ru?.recommendation || '',
          madeof: viewData.ru?.madeof || '',
          alc: viewData.ru?.alc || '',
          sugar: viewData.ru?.sugar || '',
          age: viewData.ru?.age || '',
          sparkling: viewData.ru?.sparkling || false,
          pairing: viewData.ru?.pairing || [],
          varietal: viewData.ru?.varietal || []
        },
        fr: {
          title: viewData.fr?.title || '',
          subtitle: viewData.fr?.subtitle || '',
          description: viewData.fr?.description || '',
          recommendation: viewData.fr?.recommendation || '',
          madeof: viewData.fr?.madeof || '',
          alc: viewData.fr?.alc || '',
          sugar: viewData.fr?.sugar || '',
          age: viewData.fr?.age || '',
          sparkling: viewData.fr?.sparkling || false,
          pairing: viewData.fr?.pairing || [],
          varietal: viewData.fr?.varietal || []
        }
      });
    }
  }, [viewData]);

  const handleChange = (e: Event) => {
    const target = e.target as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
    const { name, value, type } = target;
    
    if (type === 'checkbox') {
      const checkbox = target as HTMLInputElement;
      const [lang, field] = name.split('.');
      setFormData(prev => ({
        ...prev,
        [lang]: {
          ...prev[lang],
          [field]: checkbox.checked
        }
      }));
    } else {
      const [lang, field] = name.split('.');
      if (lang === 'vol' || lang === 'price' || lang === 'count') {
        setFormData(prev => ({
          ...prev,
          [lang]: Number(value)
        }));
      } else if (lang === 'image_id' || lang === 'category' || lang === 'country' || lang === 'region') {
        setFormData(prev => ({
          ...prev,
          [lang]: value
        }));
      } else {
        setFormData(prev => ({
          ...prev,
          [lang]: {
            ...prev[lang],
            [field]: value
          }
        }));
      }
    }
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Extract drink-related fields from formData
      const { en, ru, fr, category, country, ...itemFields } = formData;
      
      // Update Item fields
      const itemUpdateData = {
        vol: itemFields.vol,
        price: itemFields.price,
        count: itemFields.count,
        image_id: itemFields.image_id,
        // Note: drink_id, category, and country are not updated here as they're part of the Drink model
      };
      
      await apiClient(`/items/${id}`, {
        method: 'PATCH',
        body: itemUpdateData
      });
      
      // Update Drink fields if we have drink_id available
      if (data && data.drink && data.drink.id) {
        const drinkUpdateData = {
          title: en.title,
          title_ru: en.title_ru || en.title,
          title_fr: en.title_fr || en.title,
          subtitle: en.subtitle,
          subtitle_ru: en.subtitle_ru || en.subtitle,
          subtitle_fr: en.subtitle_fr || en.subtitle,
          description: en.description,
          description_ru: en.description_ru || en.description,
          description_fr: en.description_fr || en.description,
          recommendation: en.recommendation,
          recommendation_ru: en.recommendation_ru || en.recommendation,
          recommendation_fr: en.recommendation_fr || en.recommendation,
          madeof: en.madeof,
          madeof_ru: en.madeof_ru || en.madeof,
          madeof_fr: en.madeof_fr || en.madeof,
          alc: en.alc,
          sugar: en.sugar,
          age: en.age,
          subcategory_id: itemFields.category, // This should be from the form
          subregion_id: itemFields.region,     // This should be from the form
          sweetness_id: itemFields.sweetness_id, // This might need to be handled differently
        };
        
        await apiClient(`/drinks/${data.drink.id}`, {
          method: 'PATCH',
          body: drinkUpdateData
        });
      }
      
      showNotification('Item updated successfully', 'success');
      route(`/items/${id}`);
    } catch (error) {
      console.error('Error updating item:', error);
      showNotification(`Error updating item: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  if (loadingItem) {
    return (
      <div className="flex justify-center items-center h-64">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (errorItem) {
    return (
      <div className="alert alert-error">
        <div>
          <span>Error: {errorItem}</span>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="alert alert-warning">
        <div>
          <span>Item not found</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Edit Item</h1>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Basic Information */}
          <div className="card bg-base-100 shadow">
            <div className="card-body">
              <h2 className="card-title">Basic Information</h2>
              <div className="space-y-4">
                <div>
                  <label className="label">
                    <span className="label-text">Volume (ml)</span>
                  </label>
                  <input
                    type="number"
                    name="vol"
                    value={formData.vol}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    required
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Price (€)</span>
                  </label>
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    required
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Count</span>
                  </label>
                  <input
                    type="number"
                    name="count"
                    value={formData.count}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    required
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Image ID</span>
                  </label>
                  <input
                    type="text"
                    name="image_id"
                    value={formData.image_id}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="MongoDB image ID"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Category</span>
                  </label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange as any}
                    className="select select-bordered w-full"
                    required
                  >
                    <option value="">Select a category</option>
                    {handbooks.categories.map(cat => (
                      <option key={cat.id} value={cat.id}>
                        {cat.name || cat.name_en || cat.name_ru || cat.name_fr}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Country</span>
                  </label>
                  <select
                    name="country"
                    value={formData.country}
                    onChange={handleChange as any}
                    className="select select-bordered w-full"
                    required
                  >
                    <option value="">Select a country</option>
                    {handbooks.countries.map(country => (
                      <option key={country.id} value={country.id}>
                        {country.name || country.name_en || country.name_ru || country.name_fr}
                      </option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Region</span>
                  </label>
                  <select
                    name="region"
                    value={formData.region}
                    onChange={handleChange as any}
                    className="select select-bordered w-full"
                  >
                    <option value="">Select a region (optional)</option>
                    {handbooks.regions.map(region => (
                      <option key={region.id} value={region.id}>
                        {region.name || region.name_en || region.name_ru || region.name_fr}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* EN Language Fields */}
          <div className="card bg-base-100 shadow">
            <div className="card-body">
              <h2 className="card-title">English Fields</h2>
              <div className="space-y-4">
                <div>
                  <label className="label">
                    <span className="label-text">Title</span>
                  </label>
                  <input
                    type="text"
                    name="en.title"
                    value={formData.en.title}
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
                    name="en.subtitle"
                    value={formData.en.subtitle}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Description</span>
                  </label>
                  <textarea
                    name="en.description"
                    value={formData.en.description}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Recommendation</span>
                  </label>
                  <textarea
                    name="en.recommendation"
                    value={formData.en.recommendation}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Made Of</span>
                  </label>
                  <input
                    type="text"
                    name="en.madeof"
                    value={formData.en.madeof}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Alcohol (%)</span>
                  </label>
                  <input
                    type="text"
                    name="en.alc"
                    value={formData.en.alc}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="e.g., 13%"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Sugar (%)</span>
                  </label>
                  <input
                    type="text"
                    name="en.sugar"
                    value={formData.en.sugar}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="e.g., 5%"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Age</span>
                  </label>
                  <input
                    type="text"
                    name="en.age"
                    value={formData.en.age}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="e.g., 2019"
                  />
                </div>
                
                <div className="form-control">
                  <label className="label cursor-pointer">
                    <span className="label-text">Sparkling</span>
                    <input
                      type="checkbox"
                      name="en.sparkling"
                      checked={formData.en.sparkling}
                      onChange={handleChange as any}
                      className="checkbox checkbox-primary"
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* RU Language Fields */}
          <div className="card bg-base-100 shadow">
            <div className="card-body">
              <h2 className="card-title">Russian Fields</h2>
              <div className="space-y-4">
                <div>
                  <label className="label">
                    <span className="label-text">Title</span>
                  </label>
                  <input
                    type="text"
                    name="ru.title"
                    value={formData.ru.title}
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
                    name="ru.subtitle"
                    value={formData.ru.subtitle}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Description</span>
                  </label>
                  <textarea
                    name="ru.description"
                    value={formData.ru.description}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Recommendation</span>
                  </label>
                  <textarea
                    name="ru.recommendation"
                    value={formData.ru.recommendation}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Made Of</span>
                  </label>
                  <input
                    type="text"
                    name="ru.madeof"
                    value={formData.ru.madeof}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Alcohol (%)</span>
                  </label>
                  <input
                    type="text"
                    name="ru.alc"
                    value={formData.ru.alc}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="e.g., 13%"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Sugar (%)</span>
                  </label>
                  <input
                    type="text"
                    name="ru.sugar"
                    value={formData.ru.sugar}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="e.g., 5%"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Age</span>
                  </label>
                  <input
                    type="text"
                    name="ru.age"
                    value={formData.ru.age}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="e.g., 2019"
                  />
                </div>
                
                <div className="form-control">
                  <label className="label cursor-pointer">
                    <span className="label-text">Sparkling</span>
                    <input
                      type="checkbox"
                      name="ru.sparkling"
                      checked={formData.ru.sparkling}
                      onChange={handleChange as any}
                      className="checkbox checkbox-primary"
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* FR Language Fields */}
          <div className="card bg-base-100 shadow">
            <div className="card-body">
              <h2 className="card-title">French Fields</h2>
              <div className="space-y-4">
                <div>
                  <label className="label">
                    <span className="label-text">Title</span>
                  </label>
                  <input
                    type="text"
                    name="fr.title"
                    value={formData.fr.title}
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
                    name="fr.subtitle"
                    value={formData.fr.subtitle}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Description</span>
                  </label>
                  <textarea
                    name="fr.description"
                    value={formData.fr.description}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Recommendation</span>
                  </label>
                  <textarea
                    name="fr.recommendation"
                    value={formData.fr.recommendation}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-full"
                    rows={3}
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Made Of</span>
                  </label>
                  <input
                    type="text"
                    name="fr.madeof"
                    value={formData.fr.madeof}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Alcohol (%)</span>
                  </label>
                  <input
                    type="text"
                    name="fr.alc"
                    value={formData.fr.alc}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="e.g., 13%"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Sugar (%)</span>
                  </label>
                  <input
                    type="text"
                    name="fr.sugar"
                    value={formData.fr.sugar}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="e.g., 5%"
                  />
                </div>
                
                <div>
                  <label className="label">
                    <span className="label-text">Age</span>
                  </label>
                  <input
                    type="text"
                    name="fr.age"
                    value={formData.fr.age}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="e.g., 2019"
                  />
                </div>
                
                <div className="form-control">
                  <label className="label cursor-pointer">
                    <span className="label-text">Sparkling</span>
                    <input
                      type="checkbox"
                      name="fr.sparkling"
                      checked={formData.fr.sparkling}
                      onChange={handleChange as any}
                      className="checkbox checkbox-primary"
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <button 
            type="submit" 
            className={`btn btn-primary ${loading ? 'loading' : ''}`}
            disabled={loading}
          >
            {loading ? 'Updating...' : 'Update Item'}
          </button>
          <Link href={`/items/${id}`} variant="ghost">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
};