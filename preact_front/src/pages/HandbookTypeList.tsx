// src/pages/HandbookTypeList.tsx
// используется для отображения содержимого конкретного выбранного справочника
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { useRoute } from 'preact-iso';
import { apiClient } from '../lib/apiClient';
import { Link } from '../components/Link';

interface HandbookItem {
  id: number | string;
  name: string;
}

interface ApiResponse {
  items: HandbookItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
  has_prev: boolean;
}

export const HandbookTypeList = () => {
  const { params } = useRoute();
  const type = params.type;

  const [data, setData] = useState<HandbookItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Состояние ввода в инпуте
  const [searchInput, setSearchInput] = useState('');
  // Состояние реально примененного поиска для API
  const [appliedSearch, setAppliedSearch] = useState('');

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const pageSize = 20;

  // Сброс при смене типа справочника
  useEffect(() => {
    setPage(1);
    setSearchInput('');
    setAppliedSearch('');
  }, [type]);

  // Загрузка данных
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        // Формируем URL. Параметры lang и прочее добавятся внутри apiClient или эндпоинта
        const queryPath = `/${type}/all?page=${page}&page_size=${pageSize}&search=${encodeURIComponent(appliedSearch)}`;

        // ВЫЗОВ КАК ФУНКЦИИ (исправлено)
        const response = await apiClient<ApiResponse>(queryPath);

        setData(response.items || []);
        setTotal(response.total || 0);
        setHasNext(response.has_next || false);
        setHasPrev(response.has_prev || false);
      } catch (error) {
        console.error("Fetch error:", error);
        setData([]);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [type, page, appliedSearch]);

  const handleSearchClick = () => {
    setPage(1);
    setAppliedSearch(searchInput);
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearchClick();
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold uppercase">{type}</h1>
          <p className="text-sm opacity-60">Всего: {total}</p>
        </div>

        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Поиск..."
            className="p-2 border border-gray-300 rounded bg-base-100 focus:ring-2 focus:ring-blue-500 outline-none"
            value={searchInput}
            onInput={(e) => setSearchInput((e.target as HTMLInputElement).value)}
            onKeyDown={handleKeyDown}
          />
          <button
            onClick={handleSearchClick}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded font-medium transition-colors"
          >
            Найти
          </button>
          <Link href={`/handbooks/${type}/create`} className="btn btn-primary px-4 py-2">
            Создать
          </Link>
        </div>
      </div>

      <div className="bg-base-100 shadow-xl rounded-lg border border-gray-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="p-4 w-24">ID</th>
              <th className="p-4">Название</th>
              <th className="p-4 text-right">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {loading ? (
              <tr><td colSpan={3} className="p-10 text-center text-gray-400">Загрузка...</td></tr>
            ) : data.length > 0 ? (
              data.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="p-4 text-xs font-mono text-gray-400">{item.id}</td>
                  <td className="p-4 font-medium">{item.name}</td>
                  <td className="p-4 text-right">
                    <Link href={`/handbooks/${type}/edit/${item.id}`} className="text-blue-600 hover:underline text-sm">
                      Изменить
                    </Link>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={3} className="p-10 text-center text-gray-400">Ничего не найдено</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Пагинация */}
      <div className="flex items-center justify-center gap-4 py-4">
        <button
          className={`px-4 py-2 border rounded ${!hasPrev || loading ? 'opacity-30 cursor-not-allowed' : 'hover:bg-gray-100'}`}
          disabled={!hasPrev || loading}
          onClick={() => setPage(p => p - 1)}
        >
          Назад
        </button>

        <span className="text-sm">
          Стр. {page} из {totalPages}
        </span>

        <button
          className={`px-4 py-2 border rounded ${!hasNext || loading ? 'opacity-30 cursor-not-allowed' : 'hover:bg-gray-100'}`}
          disabled={!hasNext || loading}
          onClick={() => setPage(p => p + 1)}
        >
          Вперед
        </button>
      </div>
    </div>
  );
};
