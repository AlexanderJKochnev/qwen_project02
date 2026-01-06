// src/pages/HandbookTypeList.tsx
import { h, useState } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { Link } from '../components/Link';
import { useApi } from '../hooks/useApi';
import { useLanguage } from '../contexts/LanguageContext';
import { deleteItem } from '../lib/apiClient';
import { useNotification } from '../hooks/useNotification';

export const HandbookTypeList = () => {
  const { path } = useLocation();
  // Extract handbook type from path: /handbooks/:type -> type is the 3rd segment
  const pathSegments = path.split('/').filter(segment => segment.trim() !== '');
  // Looking for pattern: ['handbooks', 'type'] -> type is at index 1
  const type = pathSegments.length >= 2 && pathSegments[0] === 'handbooks' ? pathSegments[1] : undefined;
  const [search, setSearch] = useState('');
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<any>(null);

  const { language } = useLanguage();
  const { showNotification } = useNotification();

  // Determine the endpoint based on the handbook type
  const getEndpoint = (type: string) => {
    const endpoints: Record<string, string> = {
      'categories': `/handbooks/categories/${language}`,
      'countries': `/handbooks/countries/${language}`,
      'subcategories': `/handbooks/subcategories/${language}`,
      'subregions': `/handbooks/subregions/${language}`,
      'sweetness': `/handbooks/sweetness/${language}`,
      'foods': `/handbooks/foods/${language}`,
      'varietals': `/handbooks/varietals/${language}`,
      'superfoods': `/handbooks/superfoods/${language}`,
    };
    return endpoints[type] || `/handbooks/${type}/${language}`;
  };

  const { data, loading, error, refetch } = useApi<any[]>(
    type ? getEndpoint(type) : '', // Don't make API call if type is empty
    'GET',
    undefined,
    undefined,
    !!type // Only auto-fetch if type is defined
  );

  // Check if type is valid
  if (!type) {
    return (
      <div className="alert-error">
        <div>
          <span>Error: Invalid handbook type. Please select a valid handbook from the menu.</span>
        </div>
      </div>
    );
  }

  // Get the readable name for the handbook type
  const getReadableName = (type: string) => {
    const names: Record<string, string> = {
      'categories': 'Categories',
      'countries': 'Countries',
      'subcategories': 'Subcategories',
      'regions': 'Regions',
      'subregions': 'Subregions',
      'sweetness': 'Sweetnesses',
      'foods': 'Foods',
      'varietals': 'Varietals',
      'superfoods': 'Superfoods',
    };
    return names[type] || type.charAt(0).toUpperCase() + type.slice(1) + 's';
  };

  const handleDeleteClick = (item: any) => {
    setItemToDelete(item);
    setShowConfirmDialog(true);
  };

  const handleDelete = async () => {
    if (!itemToDelete) return;

    const deleteEndpoint = `/delete/${type}/${itemToDelete.id}`;
    const success = await deleteItem(deleteEndpoint);
    if (success) {
      showNotification('Item deleted successfully', 'success');
      refetch(); // Refresh the data
    } else {
      showNotification('Failed to delete item', 'error');
    }
    setShowConfirmDialog(false);
    setItemToDelete(null);
  };

  // Filter data based on search
  const filteredData = data?.filter(item => {
    const searchTerm = search.toLowerCase();
    return (
      (item.name && item.name.toLowerCase().includes(searchTerm)) ||
      (item.name_en && item.name_en.toLowerCase().includes(searchTerm)) ||
      (item.name_ru && item.name_ru.toLowerCase().includes(searchTerm)) ||
      (item.name_fr && item.name_fr.toLowerCase().includes(searchTerm)) ||
      (item.description && item.description.toLowerCase().includes(searchTerm)) ||
      (item.id && item.id.toString().includes(searchTerm))
    );
  }) || [];

  // Sort filtered data by name in ascending order, considering the current language
  const sortedFilteredData = [...filteredData].sort((a, b) => {
    const nameA = (a.name || '').toString().toLowerCase();
    const nameB = (b.name || '').toString().toLowerCase();

    if (nameA < nameB) return -1;
    if (nameA > nameB) return 1;
    return 0;
  });

  if (loading) {
    return (
      <div className="flex-center h-64">
        <span className="loading-spinner"></span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert-error">
        <div>
          <span>Error: {error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <h1 className="text-2xl font-bold">{getReadableName(type)}</h1>
        <Link href={`/handbooks/${type}/create`} variant="primary">
          Create New {getReadableName(type).slice(0, -1)}
        </Link>
      </div>

      <div className="flex items-center gap-2">
        <input
          type="text"
          placeholder={`Search ${getReadableName(type).toLowerCase()}...`}
          className="border rounded-l px-3 py-1.5 w-full max-w-xs border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          // className="input-bordered w-full max-w-xs"
          value={search}
          onInput={(e) => {
            const target = e.target as HTMLInputElement;
            setSearch(target.value);
          }}
        />
      </div>

      <div className="overflow-x-auto">
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {sortedFilteredData.map(item => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td>
                  <Link href={`/handbooks/${type}/${item.id}`} variant="link">
                    {item.name}
                  </Link>
                </td>
                <td>
                  <div className="flex gap-2">
                    <Link href={`/handbooks/${type}/edit/${item.id}`} variant="warning">
                      Edit
                    </Link>
                    <button
                      className="btn btn-primary"
                      onClick={() => handleDeleteClick(item)}
                    >
                      Delete
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {sortedFilteredData.length === 0 && (
        <div className="text-center py-8">
          <p>No {getReadableName(type).toLowerCase()} found.</p>
        </div>
      )}

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg">Confirm Delete</h3>
            <p className="py-4">Are you sure you want to delete this {itemToDelete ? getReadableName(type).slice(0, -1).toLowerCase() : ''}?</p>
            <div className="modal-action">
              <button
                className="btn btn-error"
                onClick={handleDelete}
              >
                Yes, Delete
              </button>
              <button
                className="btn"
                onClick={() => setShowConfirmDialog(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};