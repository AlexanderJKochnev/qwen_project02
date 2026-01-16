// src/pages/HandbookList.tsx
import { h, useState } from 'preact/hooks';
import { Link } from '../components/Link';
import { apiClient } from '../lib/apiClient';

export const HandbookList = () => {
  const [handbooks, setHandbooks] = useState([
    { id: 'categories', name: 'Categories', endpoint: '/categories/all' },
    { id: 'countries', name: 'Countries', endpoint: '/countries/all' },
    { id: 'regions', name: 'Regions', endpoint: '/regions/all' },
    { id: 'subcategories', name: 'Subcategories', endpoint: '/subcategories/all' },
    { id: 'subregions', name: 'Subregions', endpoint: '/subregions/all' },
    { id: 'sweetness', name: 'Sweetness', endpoint: '/sweetness/all' },
    { id: 'superfoods', name: 'Superfoods', endpoint: '/superfoods/all' },
    { id: 'foods', name: 'Foods', endpoint: '/foods/all' },
    { id: 'varietals', name: 'Varietals', endpoint: '/varietals/all' }
  ]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Reference Books</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {handbooks.map(handbook => (
          <div key={handbook.id} className="card bg-base-100 shadow-xl">
            <div className="card-body">
              <h2 className="card-title">{handbook.name}</h2>
              <p>Manage {handbook.name.toLowerCase()} in the reference book</p>
              <div className="card-actions justify-end">
                <Link 
                  href={`/handbooks/${handbook.id}`} 
                  className="btn btn-primary"
                >
                  View {handbook.name}
                </Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};