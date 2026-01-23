// src/components/ItemCreateForm.tsx
import { h, useState, useEffect } from 'preact/hooks';
import { apiClient } from '../lib/apiClient';
import { useLanguage } from '../contexts/LanguageContext';

interface ItemCreateFormProps {
  onClose: () => void;
  onCreated?: () => void;
}

export const ItemCreateForm = ({ onClose, onCreated }: ItemCreateFormProps) => {
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
          return { id: parseInt(id), percentage: parseFloat(percentage) };
        }).filter(v => !isNaN(v.id) && !isNaN(v.percentage)),
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

      if (onCreated) {
        onCreated();
      }
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
                    lang="ru"
                    value={formData.subtitle_ru}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Подзаголовок на Русском"
                  />
                </div>

                <div>
                  <label className="label">
                    <span className="label-text">Subtitle (French)</span>
                  </label>
                  <input
                    type="text"
                    name="subtitle_fr"
                    inputmode="latin"
                    value={formData.subtitle_fr}
                    onInput={handleChange}
                    className="input input-bordered w-full"
                    placeholder="Sous-titre en Francais"
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
                    placeholder="Volume"
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
                    placeholder="Price"
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
                    placeholder="Alcohol (%)"
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
                    placeholder="Sugar (%)"
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
                    placeholder="Age"
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
                    placeholder="Description"
                    rows={3}
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
                    placeholder="Описание на Русском"
                    rows={3}
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
                    placeholder="Description en Francais"
                    rows={3}
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
                    placeholder="Recommendation"
                    rows={3}
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
                    placeholder="Рекомендация на Русском"
                    rows={3}
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
                    placeholder="Recommandation en Francais"
                    rows={3}
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
                    placeholder="Made Of"
                    rows={3}
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
                    placeholder="Состав на Русском"
                    rows={3}
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
                    placeholder="Composition en Francais"
                    rows={3}
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
                          {varietal.name || varietal.name_en || varietal.name_ru || varietal.name_fr || varietal.name_es || varietal.name_it || varietal.name_de || varietal.name_zh}
                              {/* lang varietal.name */}
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
                </details>
              </div>
              </div>
            <div className="card bg-base-100 shadow">
              <details><summary> Foods </summary>
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
                          {food.name || food.name_en || food.name_ru || food.name_fr || food.name_es || food.name_it || food.name_de || food.name_zh}
                          {/* lang food.name */}
                        </label>
                      </div>
                    ))}
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
              {loading ? 'Creating...' : 'Create Item'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};