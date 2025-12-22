// src/pages/HandbookCreateForm.tsx
import { h, useState } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { Link } from '../components/Link';
import { useApi } from '../hooks/useApi';
import { apiClient } from '../lib/apiClient';
import { useNotification } from '../hooks/useNotification';
import { useLanguage } from '../contexts/LanguageContext';


// Добавьте интерфейс для пропсов, которые передает Router
interface HandbookCreateFormProps {
    type?: string;
}


export const HandbookCreateForm = (props: HandbookCreateFormProps) => {
  // const { path } = useLocation();
  // const match = path.match(/^\/handbooks\/([^\/]+)\/create$/);
  // const type = match ? match[1] : undefined;
  const { type } = props; // Используем props напрямую
  const { route } = useLocation(); // useLocation() все еще нужен для навигации после submit
  // Check if type is valid
  if (!type) {
    return (
      <div className="alert-error">
        <div>
          {/* Обновите сообщение об ошибке */}
          <span>Error: Handbook type is missing. Expected format: /handbooks/type/create</span>
        </div>
      </div>
    );
  }
  
  const { language } = useLanguage();
  // const { route } = useLocation();
  const { showNotification } = useNotification();
  
  // Additional API calls for dropdowns based on the model type
  const { data: countriesData, loading: loadingCountries } = useApi<any[]>(
    type === 'regions' ? '/handbooks/countries/ru' : null,
    'GET',
    undefined,
    undefined,
    type === 'regions'
  );

  const { data: categoriesData, loading: loadingCategories } = useApi<any[]>(
    type === 'subcategories' ? '/handbooks/categories/ru' : null,
    'GET',
    undefined,
    undefined,
    type === 'subcategories'
  );

  const { data: regionsData, loading: loadingRegions } = useApi<any[]>(
    type === 'subregions' ? '/handbooks/regions/ru' : null,
    'GET',
    undefined,
    undefined,
    type === 'subregions'
  );

  const { data: superfoodsData, loading: loadingSuperfoods } = useApi<any[]>(
    type === 'foods' ? '/handbooks/superfoods/ru' : null,
    'GET',
    undefined,
    undefined,
    type === 'foods'
  );
  
  const [formData, setFormData] = useState({
    name: '',
    name_ru: '',
    name_fr: '',
    description: '',
    description_ru: '',
    description_fr: '',
    country_id: undefined,
    category_id: undefined,
    region_id: undefined,
    superfood_id: undefined
  });
  const [loading, setLoading] = useState(false);

  const handleChange = (e: Event) => {
    const target = e.target as HTMLInputElement | HTMLTextAreaElement;
    const { name, value } = target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Get the readable name for the handbook type
  const getReadableName = (type: string) => {
    const names: Record<string, string> = {
      'categories': 'Category',
      'countries': 'Country',
      'regions': 'Region',
      'subcategories': 'Subcategory',
      'subregions': 'Subregion',
      'sweetness': 'Sweetness',
      'superfoods': 'Superfood',
      'foods': 'Food',
      'varietals': 'Varietal',
    };
    return names[type] || (type && type.charAt(0).toUpperCase() + type.slice(1)) || 'Unknown';
  };

  // Determine the endpoint based on the handbook type
  const getEndpoint = (type: string) => {
    const endpoints: Record<string, string> = {
      'categories': '/create/categories',
      'countries': '/create/countries',
      'regions': '/create/regions',
      'subcategories': '/create/subcategories',
      'subregions': '/create/subregions',
      'sweetness': '/create/sweetness',
      'superfoods': '/create/superfoods',
      'foods': '/create/foods',
      'varietals': '/create/varietals',
    };
    return endpoints[type] || `/create/${type}`;
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await apiClient(getEndpoint(type), {
        method: 'POST',
        body: formData
      });
      showNotification(`${getReadableName(type)} created successfully`, 'success');
      route(`/handbooks/${type}`);
    } catch (error) {
      console.error(`Error creating ${type}:`, error);
      showNotification(`Error creating ${getReadableName(type)}: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Create New {getReadableName(type)}</h1>
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="card bg-base-100 shadow">
          <div className="card-body">
            <h2 className="card-title">Basic Information</h2>
            <div className="space-y-4">
              <div>
                <label className="label">
                  <span className="label-text">Name</span>
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onInput={handleChange}
                  className="input input-bordered w-full"
                  placeholder="Name"
                />
              </div>
              
              <div>
                <label className="label">
                  <span className="label-text">Name (Russian)</span>
                </label>
                <input
                  type="text"
                  name="name_ru"
                  value={formData.name_ru}
                  onInput={handleChange}
                  className="input input-bordered w-full"
                  placeholder="Name in Russian"
                />
              </div>
              
              <div>
                <label className="label">
                  <span className="label-text">Name (French)</span>
                </label>
                <input
                  type="text"
                  name="name_fr"
                  value={formData.name_fr}
                  onInput={handleChange}
                  className="input input-bordered w-full"
                  placeholder="Nom en Francais"
                />
              </div>
              
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
                  placeholder="Описание на Русском"
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
                  placeholder="Description en Francais"
                />
              </div>
              
              {/* Conditional dropdowns based on handbook type */}
              {type === 'regions' && (
                <div>
                  <label className="label">
                    <span className="label-text">Country</span>
                  </label>
                  {loadingCountries ? (
                    <select className="select select-bordered w-full" disabled>
                      <option>Loading...</option>
                    </select>
                  ) : (
                    <select
                      name="country_id"
                      value={formData.country_id || ''}
                      onChange={(e) => {
                        const target = e.target as HTMLSelectElement;
                        setFormData(prev => ({
                          ...prev,
                          country_id: target.value ? parseInt(target.value) : undefined
                        }));
                      }}
                      className="select select-bordered w-full"
                    >
                      <option value="">Select a country</option>
                      {countriesData && countriesData.map((country: any) => (
                        <option key={country.id} value={country.id}>
                          {country.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}
              
              {type === 'subcategories' && (
                <div>
                  <label className="label">
                    <span className="label-text">Category</span>
                  </label>
                  {loadingCategories ? (
                    <select className="select select-bordered w-full" disabled>
                      <option>Loading...</option>
                    </select>
                  ) : (
                    <select
                      name="category_id"
                      value={formData.category_id || ''}
                      onChange={(e) => {
                        const target = e.target as HTMLSelectElement;
                        setFormData(prev => ({
                          ...prev,
                          category_id: target.value ? parseInt(target.value) : undefined
                        }));
                      }}
                      className="select select-bordered w-full"
                    >
                      <option value="">Select a category</option>
                      {categoriesData && categoriesData.map((category: any) => (
                        <option key={category.id} value={category.id}>
                          {category.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}
              
              {type === 'subregions' && (
                <div>
                  <label className="label">
                    <span className="label-text">Region</span>
                  </label>
                  {loadingRegions ? (
                    <select className="select select-bordered w-full" disabled>
                      <option>Loading...</option>
                    </select>
                  ) : (
                    <select
                      name="region_id"
                      value={formData.region_id || ''}
                      onChange={(e) => {
                        const target = e.target as HTMLSelectElement;
                        setFormData(prev => ({
                          ...prev,
                          region_id: target.value ? parseInt(target.value) : undefined
                        }));
                      }}
                      className="select select-bordered w-full"
                    >
                      <option value="">Select a region</option>
                      {regionsData && regionsData.map((region: any) => (
                        <option key={region.id} value={region.id}>
                          {region.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}
              
              {type === 'foods' && (
                <div>
                  <label className="label">
                    <span className="label-text">Superfood</span>
                  </label>
                  {loadingSuperfoods ? (
                    <select className="select select-bordered w-full" disabled>
                      <option>Loading...</option>
                    </select>
                  ) : (
                    <select
                      name="superfood_id"
                      value={formData.superfood_id || ''}
                      onChange={(e) => {
                        const target = e.target as HTMLSelectElement;
                        setFormData(prev => ({
                          ...prev,
                          superfood_id: target.value ? parseInt(target.value) : undefined
                        }));
                      }}
                      className="select select-bordered w-full"
                    >
                      <option value="">Select a superfood</option>
                      {superfoodsData && superfoodsData.map((superfood: any) => (
                        <option key={superfood.id} value={superfood.id}>
                          {superfood.name}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <button 
            type="submit" 
            className={`btn btn-primary ${loading ? 'loading' : ''}`}
            disabled={loading}
          >
            {loading ? `Creating ${getReadableName(type)}...` : `Create ${getReadableName(type)}`}
          </button>
          <Link href={`/handbooks/${type}`} variant="ghost">
            Cancel
          </Link>
        </div>
      </form>
    </div>
  );
};