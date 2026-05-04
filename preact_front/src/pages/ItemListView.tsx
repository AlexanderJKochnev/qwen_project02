// src/pages/ItemListView.tsx
import { h } from 'preact'; // Исправлено: h из preact
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
  // --- БЛОК 1: СУЩЕСТВУЮЩЕЕ СОСТОЯНИЕ (БЕЗ ИЗМЕНЕНИЙ) ---
  const [viewMode, setViewMode] = useState<'table' | 'grid'>(() => {
    const savedViewMode = localStorage.getItem('itemListViewMode');
    return savedViewMode === 'table' || savedViewMode === 'grid' ? savedViewMode : 'table';
  });
  const [search, setSearch] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [gridColumns, setGridColumns] = useState(3);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [itemToDelete, setItemToDelete] = useState<number | null>(null);

  // --- БЛОК 2: НОВОЕ СОСТОЯНИЕ KEYSET ПАГИНАЦИИ ---
  // Вместо page используем объект курсора
  const [cursor, setCursor] = useState<{ score: string | null; id: number | null }>({
    score: null,
    id: null
  });
  // Стек для реализации кнопки "Назад" (храним предыдущие курсоры)
  const [history, setHistory] = useState<Array<{ score: string | null; id: number | null }>>([]);

  const { language } = useLanguage();
  const { showNotification } = useNotification();

  // --- БЛОК 3: ОБНОВЛЕННЫЙ ЗАПРОС К API ---
  const { data, loading, error, refetch } = useApi<PaginatedResponse<ItemRead>>(
    `/search_smart_page/${language}`, // Путь к твоему новому эндпоинту
    'GET',
    undefined,
    {
      query: searchQuery,
      last_score: cursor.score,
      last_id: cursor.id,
      limit: 12
    }
  );

  // --- БЛОК 4: ОБРАБОТЧИКИ СОБЫТИЙ ---
  useEffect(() => {
    localStorage.setItem('itemListViewMode', viewMode);
  }, [viewMode]);

  const handleSearchSubmit = (e: Event) => {
    e.preventDefault();
    setSearchQuery(search.trim());
    setCursor({ score: null, id: null }); // Сброс при поиске
    setHistory([]); // Очистка истории
  };

  // Прыжок вперед по якорю
  const handleJump = (anchor: any) => {
    setHistory([...history, cursor]); // Сохраняем текущий, чтобы вернуться
    setCursor({ score: anchor.last_score, id: anchor.last_id });
  };

  // Возврат назад
  const handleGoBack = () => {
    const newHistory = [...history];
    const prevCursor = newHistory.pop();
    if (prevCursor !== undefined) {
      setCursor(prevCursor);
      setHistory(newHistory);
    }
  };

  // --- БЛОК 5: ЛОГИКА УДАЛЕНИЯ (БЕЗ ИЗМЕНЕНИЙ) ---
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
  if (error) return <div className="alert alert-error"><span>Error: {error}</span></div>;

  return (
    <div className="space-y-6 w-full">
      {/* HEADER & SEARCH (БЕЗ ИЗМЕНЕНИЙ) */}
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
            <button type="submit" className="btn btn-primary rounded-l-none -ml-1">Search</button>
          </form>
          <div className="flex gap-2">
            <button className={`btn ${viewMode === 'table' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setViewMode('table')}>Table</button>
            <button className={`btn ${viewMode === 'grid' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setViewMode('grid')}>Grid</button>
          </div>
        </div>
      </div>

      {/* ОСНОВНОЙ КОНТЕНТ (БЕЗ ИЗМЕНЕНИЙ, только замена data.items) */}
      {viewMode === 'table' ? (
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr>
                <th>Image</th><th>Title</th><th>Category</th><th>Price</th><th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data?.items?.map(item => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td><ItemImage image_id={item.image_id} size="small" /></td>
                  <td><Link href={`/items/${item.id}`} variant="link">{item.title}</Link></td>
                  <td>{item.category}</td>
                  <td>{item.price ? `€${item.price}` : 'N/A'}</td>
                  <td>
                    <div className="flex gap-2">
                      <button className="btn btn-error btn-sm" onClick={() => handleDeleteClick(item.id)}>Delete</button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className={`grid grid-cols-1 md:grid-cols-${gridColumns} gap-4`}>
          {data?.items?.map(item => (
            <div key={item.id} className="card bg-base-100 shadow-xl">
              <figure className="px-10 pt-10"><ItemImage image_id={item.image_id} size="medium" /></figure>
              <div className="card-body">
                <h2 className="card-title">{item.title}</h2>
                <div className="card-actions justify-end">
                  <button className="btn btn-error btn-sm" onClick={() => handleDeleteClick(item.id)}>Delete</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* НОВЫЙ БЛОК ПАГИНАЦИИ (ЯКОРЯ) */}
      <div className="flex justify-center items-center gap-2 mt-8">
        {history.length > 0 && (
          <button className="btn btn-outline" onClick={handleGoBack}>← Назад</button>
        )}

        {data?.anchors?.map((anchor: any) => (
          <button
            key={`${anchor.last_id}-${anchor.last_score}`}
            className="btn btn-primary btn-outline"
            onClick={() => handleJump(anchor)}
          >
            +{anchor.page_offset} стр.
          </button>
        ))}
      </div>

      {/* CONFIRM DIALOG (БЕЗ ИЗМЕНЕНИЙ) */}
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
