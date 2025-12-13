// src/pages/ItemDetailView.tsx
import { h, useState, useEffect } from 'preact/hooks';
import { useLocation } from 'preact-iso';
import { Link } from '../components/Link';
import { useApi } from '../hooks/useApi';
import { ItemImage } from '../components/ItemImage';
import { deleteItem } from '../lib/apiClient';
import { useNotification } from '../hooks/useNotification';
import { useLanguage } from '../contexts/LanguageContext';

// Define the expected response type from backend according to requirements
interface ItemDetailResponse {
  id: number;
  vol: number;
  alc: string;
  age: string;
  image_id: string;
  title: string;
  subtitle: string;
  country: string;
  category: string;
  sweetness: string;
  recommendation: string;
  madeof: string;
  description: string;
  varietal: string[];
  pairing: string[];
  [key: string]: any; // Allow for additional fields
}

export const ItemDetailView = () => {
  const { url, route } = useLocation();
  // Extract ID from URL path - expecting format like /items/123
  const pathParts = url.split('/');
  const idParam = pathParts[pathParts.length - 1]; // Get the last part of the path
  const id = parseInt(idParam);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
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
  
  const { data, loading, error, refetch } = useApi<ItemDetailResponse>(
    `/detail/${language}/${id}`,
    'GET'
  );

  const handleDelete = async () => {
    const success = await deleteItem(`/delete/items/${id}`);
    if (success) {
      showNotification('Item deleted successfully', 'success');
      route('/items');
    } else {
      showNotification('Failed to delete item', 'error');
    }
    setShowConfirmDialog(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <span className="loading loading-spinner loading-lg"></span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error">
        <div>
          <span>Error: {error}</span>
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

  // Helper function to check if a value is empty (null, undefined, empty string, NaN)
  const isEmpty = (value: any): boolean => {
    if (value === null || value === undefined) return true;
    if (typeof value === 'string' && value.trim() === '') return true;
    if (typeof value === 'number' && isNaN(value)) return true;
    if (Array.isArray(value) && value.length === 0) return true;
    return false;
  };

  // Get all fields from the data object that are not empty
  const nonEmptyFields = Object.entries(data).filter(([key, value]) => !isEmpty(value));

  return (
    <div className="detail-view">
      <div className="flex justify-between items-center">
        <div className="flex gap-2">
          <h1 className="text-2xl font-bold">
            {data.title || 'Item Detail'}
          </h1>
        </div>
        <div className="flex gap-2">
          <Link href={`/items/edit/${id}`} variant="primary">
            Edit
          </Link>
          <button 
            className="btn btn-primary"
            onClick={() => setShowConfirmDialog(true)}
          >
            Delete
          </button>
          <button
            className="btn btn-primary"
            onClick={() => route('/items')}
          >
            Back
          </button>
        </div>
      </div>

      <div className="detail-content-layout">
        <div className="fixed-block">
          <figure>
             <ItemImage image_id={data.image_id} size="large" />
          </figure>
        </div>
        <div className="flexible-block">
          <div className="card bg-base-100 shadow">
            <div className="card-body">
              <table className="parameter-table">
                <tbody>
                  {nonEmptyFields.map(([key, value]) => {
                    // Skip id and image_id as they are used elsewhere
                    if (key === 'id' || key === 'image_id') return null;
                    
                    // Format the field name for display
                    const displayName = key
                      .split('_')
                      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                      .join(' ');

                    return (
                      <tr key={key}>
                        <td className="param-label">{displayName}</td>
                        <td className="param-value">
                          {Array.isArray(value) ? (
                            <ul className="list-disc pl-5">
                              {value.map((item, index) => (
                                <li key={index}>{item}</li>
                              ))}
                            </ul>
                          ) : (
                            <span>{value}</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        
        {/* Parameters card section - only for mobile screens */}
        <div className="w-full lg:hidden">
          {nonEmptyFields.map(([key, value]) => {
            // Skip id and image_id as they are used elsewhere
            if (key === 'id' || key === 'image_id') return null;
            
            // Format the field name for display
            const displayName = key
              .split('_')
              .map(word => word.charAt(0).toUpperCase() + word.slice(1))
              .join(' ');

            return (
              <div key={key} className="card bg-base-100 shadow mb-4">
                <div className="card-body">
                  <h2 className="card-title param-label-mobile">{displayName}</h2>
                  <div className="param-value-mobile">
                    {Array.isArray(value) ? (
                      <ul className="list-disc pl-5">
                        {value.map((item, index) => (
                          <li key={index}>{item}</li>
                        ))}
                      </ul>
                    ) : (
                      <p>{value}</p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Confirmation Dialog */}
      {showConfirmDialog && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg">Confirm Delete</h3>
            <p className="py-4">Are you sure you want to delete this item?</p>
            <div className="modal-action">
              <button 
                className="btn btn-secondary"
                onClick={handleDelete}
              >
                Yes, Delete
              </button>
              <button 
                className="btn btn-ghost"
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