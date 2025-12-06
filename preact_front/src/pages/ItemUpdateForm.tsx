// src/pages/ItemUpdateForm.tsx
import { h, useState, useEffect } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { Link } from '../components/Link';
import { useApi } from '../hooks/useApi';
import { apiClient } from '../lib/apiClient';
import { ItemRead } from '../types/item';
import { useNotification } from '../hooks/useNotification';

export const ItemUpdateForm = () => {
  const { path, route } = useLocation();
  const id = parseInt(path.split('/')[3]);
  const { showNotification } = useNotification();
  
  const { data, loading: loadingItem, error: errorItem } = useApi<ItemRead>(
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
    en: { title: '', subtitle: '', description: '', recommendation: '', madeof: '', alc: '', sugar: '', age: '', sparkling: false, pairing: [], varietal: [] },
    ru: { title: '', subtitle: '', description: '', recommendation: '', madeof: '', alc: '', sugar: '', age: '', sparkling: false, pairing: [], varietal: [] },
    fr: { title: '', subtitle: '', description: '', recommendation: '', madeof: '', alc: '', sugar: '', age: '', sparkling: false, pairing: [], varietal: [] }
  });
  const [loading, setLoading] = useState(false);
  const [handbooks, setHandbooks] = useState({
    categories: [],
    countries: [],
    subcategories: [],
    subregions: [],
    sweetnesses: [],
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
          subcategories,
          subregions,
          sweetnesses,
          foods,
          varietals
        ] = await Promise.all([
          apiClient<any[]>('/categories/all'),
          apiClient<any[]>('/countries/all'),
          apiClient<any[]>('/subcategories/all'),
          apiClient<any[]>('/subregions/all'),
          apiClient<any[]>('/sweetnesses/all'),
          apiClient<any[]>('/foods/all'),
          apiClient<any[]>('/varietals/all'),
        ]);
        setHandbooks({
          categories,
          countries,
          subcategories,
          subregions,
          sweetnesses,
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
    if (data) {
      setFormData({
        vol: data.vol || 0,
        price: data.price || 0,
        count: data.count || 0,
        image_id: data.image_id || '',
        category: data.category || '',
        country: data.country || '',
        en: {
          title: data.en?.title || '',
          subtitle: data.en?.subtitle || '',
          description: data.en?.description || '',
          recommendation: data.en?.recommendation || '',
          madeof: data.en?.madeof || '',
          alc: data.en?.alc || '',
          sugar: data.en?.sugar || '',
          age: data.en?.age || '',
          sparkling: data.en?.sparkling || false,
          pairing: data.en?.pairing || [],
          varietal: data.en?.varietal || []
        },
        ru: {
          title: data.ru?.title || '',
          subtitle: data.ru?.subtitle || '',
          description: data.ru?.description || '',
          recommendation: data.ru?.recommendation || '',
          madeof: data.ru?.madeof || '',
          alc: data.ru?.alc || '',
          sugar: data.ru?.sugar || '',
          age: data.ru?.age || '',
          sparkling: data.ru?.sparkling || false,
          pairing: data.ru?.pairing || [],
          varietal: data.ru?.varietal || []
        },
        fr: {
          title: data.fr?.title || '',
          subtitle: data.fr?.subtitle || '',
          description: data.fr?.description || '',
          recommendation: data.fr?.recommendation || '',
          madeof: data.fr?.madeof || '',
          alc: data.fr?.alc || '',
          sugar: data.fr?.sugar || '',
          age: data.fr?.age || '',
          sparkling: data.fr?.sparkling || false,
          pairing: data.fr?.pairing || [],
          varietal: data.fr?.varietal || []
        }
      });
    }
  }, [data]);

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
      } else if (lang === 'image_id' || lang === 'category' || lang === 'country') {
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
      await apiClient(`/items/${id}`, {
        method: 'PUT',
        body: formData
      });
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
          <Link href={`/items/${id}`} className="btn btn-ghost">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
};