// src/pages/ItemCreateForm.tsx
import { h, useState, useEffect } from 'preact/hooks';
import { Link } from '../components/Link';
import { useLocation } from 'preact-iso';
import { apiClient } from '../lib/apiClient';
import { useNotification } from '../hooks/useNotification';

export const ItemCreateForm = ({ path }: { path?: string }) => {
  const { route } = useLocation();
  const { showNotification } = useNotification();
  const [formData, setFormData] = useState({
    vol: 0,
    price: 0,
    count: 0,
    image_id: '',
    category: '',
    country: '',
    region: '',
    alc: '',
    sugar: '',
    age: '',
    pairing: [],
    varietal: [],
    en: { title: '', subtitle: '', description: '', recommendation: '', madeof: '', sparkling: false },
    ru: { title: '', subtitle: '', description: '', recommendation: '', madeof: '', sparkling: false },
    fr: { title: '', subtitle: '', description: '', recommendation: '', madeof: '', sparkling: false }
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
    } else if (type === 'select-multiple') {
      // Handle multi-select for pairing and varietal
      const select = target as HTMLSelectElement;
      const selectedValues = Array.from(select.selectedOptions).map(option => option.value);

      if (name === 'pairing') {
        setFormData(prev => ({
          ...prev,
          pairing: selectedValues
        }));
      } else if (name === 'varietal') {
        setFormData(prev => ({
          ...prev,
          varietal: selectedValues
        }));
      }
    } else {
      const [firstPart, field] = name.split('.');

      if (firstPart === 'vol' || firstPart === 'price' || firstPart === 'count') {
        setFormData(prev => ({
          ...prev,
          [firstPart]: Number(value)
        }));
      } else if (firstPart === 'image_id' || firstPart === 'category' || firstPart === 'country' || firstPart === 'region' ||
                 firstPart === 'alc' || firstPart === 'sugar' || firstPart === 'age') {
        setFormData(prev => ({
          ...prev,
          [firstPart]: value
        }));
      } else if (firstPart === 'pairing' || firstPart === 'varietal') {
        // Handle single selection for pairing/varietal (in case of single select dropdown)
        setFormData(prev => ({
          ...prev,
          [firstPart]: value
        }));
      } else {
        setFormData(prev => ({
          ...prev,
          [firstPart]: {
            ...prev[firstPart],
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
      await apiClient('/items', {
        method: 'POST',
        body: formData
      });
      showNotification('Item created successfully', 'success');
      route('/items');
    } catch (error) {
      console.error('Error creating item:', error);
      showNotification(`Error creating item: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Create New Item</h1>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Basic Information */}
          <div className="card bg-base-100 shadow">
            <div className="card-body">
              <h2 className="card-title">Basic Information</h2>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Volume (ml)</span>
                  </label>
                  <input
                    type="number"
                    name="vol"
                    value={formData.vol}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                    required
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Price (€)</span>
                  </label>
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                    required
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Count</span>
                  </label>
                  <input
                    type="number"
                    name="count"
                    value={formData.count}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                    required
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Image ID</span>
                  </label>
                  <input
                    type="text"
                    name="image_id"
                    value={formData.image_id}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                    placeholder="MongoDB image ID"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Category</span>
                  </label>
                  <select
                    name="category"
                    value={formData.category}
                    onChange={handleChange as any}
                    className="select select-bordered w-2/3"
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

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Country</span>
                  </label>
                  <select
                    name="country"
                    value={formData.country}
                    onChange={handleChange as any}
                    className="select select-bordered w-2/3"
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

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Region</span>
                  </label>
                  <select
                    name="region"
                    value={formData.region}
                    onChange={handleChange as any}
                    className="select select-bordered w-2/3"
                  >
                    <option value="">Select a region (optional)</option>
                    {handbooks.regions.map(region => (
                      <option key={region.id} value={region.id}>
                        {region.name || region.name_en || region.name_ru || region.name_fr}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Alcohol (%)</span>
                  </label>
                  <input
                    type="text"
                    name="alc"
                    value={formData.alc}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                    placeholder="e.g., 13%"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Sugar (%)</span>
                  </label>
                  <input
                    type="text"
                    name="sugar"
                    value={formData.sugar}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                    placeholder="e.g., 5%"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Age</span>
                  </label>
                  <input
                    type="text"
                    name="age"
                    value={formData.age}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                    placeholder="e.g., 2019"
                  />
                </div>

                <div>
                  <label className="label w-1/3 inline-block">
                    <span className="label-text">Pairing</span>
                  </label>
                  <div className="w-2/3 inline-block">
                    <select
                      name="pairing"
                      multiple
                      value={formData.pairing}
                      onChange={handleChange as any}
                      className="select select-bordered w-full h-24"
                    >
                      {handbooks.foods.map(food => (
                        <option key={food.id} value={food.id}>
                          {food.name || food.name_en || food.name_ru || food.name_fr}
                        </option>
                      ))}
                    </select>
                    <p className="text-sm text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple options</p>
                  </div>
                </div>

                <div>
                  <label className="label w-1/3 inline-block">
                    <span className="label-text">Varietal</span>
                  </label>
                  <div className="w-2/3 inline-block">
                    <select
                      name="varietal"
                      multiple
                      value={formData.varietal}
                      onChange={handleChange as any}
                      className="select select-bordered w-full h-24"
                    >
                      {handbooks.varietals.map(varietal => (
                        <option key={varietal.id} value={varietal.id}>
                          {varietal.name || varietal.name_en || varietal.name_ru || varietal.name_fr}
                        </option>
                      ))}
                    </select>
                    <p className="text-sm text-gray-500 mt-1">Hold Ctrl/Cmd to select multiple options</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* EN Language Fields */}
          <div className="card bg-base-100 shadow">
            <div className="card-body">
              <h2 className="card-title">English Fields</h2>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Title</span>
                  </label>
                  <input
                    type="text"
                    name="en.title"
                    value={formData.en.title}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Subtitle</span>
                  </label>
                  <input
                    type="text"
                    name="en.subtitle"
                    value={formData.en.subtitle}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Description</span>
                  </label>
                  <textarea
                    name="en.description"
                    value={formData.en.description}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-2/3"
                    rows={3}
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Recommendation</span>
                  </label>
                  <textarea
                    name="en.recommendation"
                    value={formData.en.recommendation}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-2/3"
                    rows={3}
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Made Of</span>
                  </label>
                  <input
                    type="text"
                    name="en.madeof"
                    value={formData.en.madeof}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Sparkling</span>
                  </label>
                  <input
                    type="checkbox"
                    name="en.sparkling"
                    checked={formData.en.sparkling}
                    onChange={handleChange as any}
                    className="checkbox checkbox-primary"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* RU Language Fields */}
          <div className="card bg-base-100 shadow">
            <div className="card-body">
              <h2 className="card-title">Russian Fields</h2>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Title</span>
                  </label>
                  <input
                    type="text"
                    name="ru.title"
                    value={formData.ru.title}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Subtitle</span>
                  </label>
                  <input
                    type="text"
                    name="ru.subtitle"
                    value={formData.ru.subtitle}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Description</span>
                  </label>
                  <textarea
                    name="ru.description"
                    value={formData.ru.description}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-2/3"
                    rows={3}
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Recommendation</span>
                  </label>
                  <textarea
                    name="ru.recommendation"
                    value={formData.ru.recommendation}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-2/3"
                    rows={3}
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Made Of</span>
                  </label>
                  <input
                    type="text"
                    name="ru.madeof"
                    value={formData.ru.madeof}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Sparkling</span>
                  </label>
                  <input
                    type="checkbox"
                    name="ru.sparkling"
                    checked={formData.ru.sparkling}
                    onChange={handleChange as any}
                    className="checkbox checkbox-primary"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* FR Language Fields */}
          <div className="card bg-base-100 shadow">
            <div className="card-body">
              <h2 className="card-title">French Fields</h2>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Title</span>
                  </label>
                  <input
                    type="text"
                    name="fr.title"
                    value={formData.fr.title}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Subtitle</span>
                  </label>
                  <input
                    type="text"
                    name="fr.subtitle"
                    value={formData.fr.subtitle}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Description</span>
                  </label>
                  <textarea
                    name="fr.description"
                    value={formData.fr.description}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-2/3"
                    rows={3}
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Recommendation</span>
                  </label>
                  <textarea
                    name="fr.recommendation"
                    value={formData.fr.recommendation}
                    onInput={handleChange}
                    className="textarea textarea-bordered w-2/3"
                    rows={3}
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Made Of</span>
                  </label>
                  <input
                    type="text"
                    name="fr.madeof"
                    value={formData.fr.madeof}
                    onInput={handleChange}
                    className="input input-bordered w-2/3"
                  />
                </div>

                <div className="flex items-center space-x-4">
                  <label className="label w-1/3">
                    <span className="label-text">Sparkling</span>
                  </label>
                  <input
                    type="checkbox"
                    name="fr.sparkling"
                    checked={formData.fr.sparkling}
                    onChange={handleChange as any}
                    className="checkbox checkbox-primary"
                  />
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
            {loading ? 'Creating...' : 'Create Item'}
          </button>
          <Link href="/items" variant="ghost">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
};