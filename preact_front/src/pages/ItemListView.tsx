// preact_front/src/pages/ItemListView.tsx
// import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { Link } from '../components/Link';
import { useApi } from '../hooks/useApi';
import { ItemRead } from '../types/item';
import { ItemImage } from '../components/ItemImage';
import { PaginatedResponse } from '../types/base';
import { useLanguage } from '../contexts/LanguageContext';
import { deleteItem } from '../lib/apiClient';
import { useNotification } from '../hooks/useNotification';

export const ItemListView = () => {
  const [viewMode, setViewMode] = useState<'table' | 'grid'>(() => {
    const savedViewMode = localStorage.getItem('itemListViewMode');
    return savedViewMode === 'table' || savedViewMode === 'grid' ? savedViewMode : 'table';
  });

  // СОСТОЯНИЕ ПАГИНАЦИИ (KEYSET)
  const [search, setSearch] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [cursor, setCursor] = useState<{ score: string | null; id: number | null }>({ score: null, id: null });
  const [history, setHistory] = useState<Array<{ score: string | null; id: number | null }>>([]);

  const [gridColumns, setGridColumns] = useState(3);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<number | null>(null);

  const { language } = useLanguage();
  const { showNotification } = useNotification();

  // ЗАПРОС К НОВОМУ ЭНДПОИНТУ
  const { data, loading, error, refetch } = useApi<PaginatedResponse<ItemRead>>(
    `/items/smart_search/${language}`,
    'GET',
    undefined,
    {
      query: searchQuery,
      last_score: cursor.score,
      last_id: cursor.id,
      limit: 12
    }
  );

  useEffect(() => {
    localStorage.setItem('itemListViewMode', viewMode);
  }, [viewMode]);

  // ОБРАБОТЧИКИ
  const handleSearchSubmit = (e: Event) => {
    e.preventDefault();
    setSearchQuery(search.trim());
    setCursor({ score: null, id: null });
    setHistory([]);
  };

  const handleJump = (anchor: any) => {
    setHistory([...history, cursor]);
    setCursor({ score: anchor.last_score, id: anchor.last_id });
  };

  const handleGoBack = () => {
    const newHistory = [...history];
    const prev = newHistory.pop();
    if (prev !== undefined) {
      setCursor(prev);
      setHistory(newHistory);
    }
  };

  const handleDeleteClick = (itemId: number) => {
    setItemToDelete(itemId);
    setShowConfirmDialog(true);
  };

  const handleDeleteConfirm = async () => {
    if (itemToDelete !== null) {
      const success = await deleteItem(`/items/${itemToDelete}`);
      if (success) {
        showNotification('Item deleted successfully', 'success');
        refetch();
      } else {
        showNotification('Failed to delete item', 'error');
      }
      setShowConfirmDialog(false);
      setItemToDelete(null);
    }
  };

  if (loading) return <div className="flex justify-center items-center h-64"><span className="loading loading-spinner loading-lg"></span></div>;
  if (error) return <div className="alert alert-error"><div><span>Error: {error}</span></div></div>;

  return (
    <div className="space-y-6 w-full">
      <div className="flex flex-row justify-between items-center gap-4">
        <h1 className="text-2xl font-bold">Items</h1>
        <Link href="/items/create" variant="primary">Create New Item</Link>
      </div>

      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div className="flex flex-col sm:flex-row gap-2 w-full md:w-auto">
          <form onSubmit={handleSearchSubmit} className="flex">
            <input
              type="text"
              placeholder="Search items..."
              className="border rounded-l px-3 py-1.5 w-full max-w-xs border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={search}
              onInput={(e) => setSearch((e.target as HTMLInputElement).value)}
            />
            <button type="submit" className="btn btn-primary rounded-l-none -ml-1 flex items-center">
              <svg xmlns="http://w3.org" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
              </svg>
              Search
            </button>
          </form>
          <div className="flex gap-2">
            <button className={`btn ${viewMode === 'table' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setViewMode('table')}>Table</button>
            <button className={`btn ${viewMode === 'grid' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setViewMode('grid')}>Grid</button>
          </div>
        </div>
      </div>

      {viewMode === 'table' ? (
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Image</th><th>Title</th><th>Category</th><th>Volume</th><th>Price</th><th>Country</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map(item => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td><ItemImage image_id={item.image_id} size="small" /></td>
                  <td><Link href={`/items/${item.id}`} variant="link">{item.title}</Link></td>
                  <td>{item.category}</td>
                  <td>{item.vol ? `${item.vol} ml` : 'N/A'}</td>
                  <td>{item.price ? `€${item.price}` : 'N/A'}</td>
                  <td>{item.country}</td>
                  <td>
                    <div className="flex gap-2">
                      <button className="btn btn-error btn-sm" onClick={() => handleDeleteClick(item.id)}>Delete</button>
                      <Link href={`/items/edit/${item.id}`} variant="link">Edit</Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className={`card-grid grid-cols-${gridColumns}`}>
          {data?.items.map(item => (
            <div key={item.id} className="card">
              <div className="h-48 flex items-center justify-center bg-gray-100">
                <ItemImage image_id={item.image_id} size="medium" />
              </div>
              <div className="p-4">
                <h2 className="text-lg font-semibold mb-2">
                  <Link href={`/items/${item.id}`} variant="link">
                    {item?.title || 'No title'}
                  </Link>
                </h2>
                <p className="text-sm text-gray-600 mb-1">Volume: {item.vol ? `${item.vol} ml` : 'N/A'}</p>
                <p className="text-sm text-red-600 mb-1">Price: {item.price ? `€${item.price}` : 'N/A'}</p>
                <p className="text-sm text-gray-600 mb-4">Country: {item.country || 'N/A'}</p>
                <div className="flex justify-end gap-2">
                  <button className="btn btn-error btn-sm" onClick={() => handleDeleteClick(item.id)}>Delete</button>
                  <Link href={`/items/edit/${item.id}`} variant="link">Edit</Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ПАГИНАЦИЯ */}
      <div className="flex justify-center items-center gap-2 mt-8 py-4">
        {history.length > 0 && <button className="btn btn-outline" onClick={handleGoBack}>← Назад</button>}
        {data?.anchors?.map((anchor: any) => (
          <button key={`${anchor.last_id}-${anchor.last_score}`} className="btn btn-primary btn-outline" onClick={() => handleJump(anchor)}>
            +{anchor.page_offset} стр.
          </button>
        ))}
      </div>

      {/* CONFIRM DIALOG */}
      {showConfirmDialog && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg">Confirm Delete</h3>
            <p className="py-4">Are you sure you want to delete this item?</p>
            <div className="modal-action">
              <button className="btn btn-error" onClick={handleDeleteConfirm}>Delete</button>
              <button className="btn" onClick={() => setShowConfirmDialog(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
