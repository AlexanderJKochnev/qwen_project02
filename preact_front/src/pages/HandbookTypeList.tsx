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

export const HandbookTypeList = () => {
  const { params } = useRoute();
  const type = params.type;

  const [data, setData] = useState<HandbookItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  // Пагинация
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [hasNext, setHasNext] = useState(false);
  const [hasPrev, setHasPrev] = useState(false);
  const pageSize = 20;

  // При смене типа или поиске — сбрасываем на 1 страницу
  useEffect(() => {
    setPage(1);
  }, [type, search]);

  useEffect(() => {
    const handler = setTimeout(() => {
      fetchData();
    }, 300); // Дебаунс поиска 300мс

    return () => clearTimeout(handler);
  }, [type, page, search]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Добавляем параметр search в запрос
      const response = await apiClient.get(
        `/${type}/all?page=${page}&page_size=${pageSize}&search=${encodeURIComponent(search)}`
      );

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

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold uppercase">{type}</h1>
          <p className="text-sm opacity-60">Найдено: {total}</p>
        </div>

        <div className="flex gap-2">
          {/* Поле поиска */}
          <input
            type="text"
            placeholder="Поиск по названию..."
            className="p-2 border border-gray-300 rounded-md bg-base-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
            value={search}
            onInput={(e) => setSearch((e.target as HTMLInputElement).value)}
          />
          <Link href={`/handbooks/${type}/create`} className="btn btn-primary px-4 py-2 flex items-center">
            Добавить
          </Link>
        </div>
      </div>

      <div className="bg-base-100 shadow-xl rounded-lg overflow-hidden border border-gray-100">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              <th className="p-4 font-semibold text-gray-600 w-24">ID</th>
              <th className="p-4 font-semibold text-gray-600">Название</th>
              <th className="p-4 font-semibold text-gray-600 text-right">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={3} className="p-10 text-center text-gray-400">Загрузка данных...</td></tr>
            ) : data.length > 0 ? (
              data.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                  <td className="p-4 text-xs font-mono text-gray-500">{item.id}</td>
                  <td className="p-4 font-medium">{item.name}</td>
                  <td className="p-4 text-right">
                    <Link
                      href={`/handbooks/${type}/edit/${item.id}`}
                      className="text-blue-600 hover:underline text-sm font-medium"
                    >
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

      {/* Пагинация без DaisyUI */}
      <div className="flex items-center justify-center gap-6 mt-4 pb-8">
        <button
          className={`px-4 py-2 rounded border ${!hasPrev || loading ? 'opacity-30 cursor-not-allowed' : 'hover:bg-gray-100'}`}
          disabled={!hasPrev || loading}
          onClick={() => setPage(p => p - 1)}
        >
          Назад
        </button>

        <span className="text-sm font-medium">
          Стр. {page} из {totalPages}
        </span>

        <button
          className={`px-4 py-2 rounded border ${!hasNext || loading ? 'opacity-30 cursor-not-allowed' : 'hover:bg-gray-100'}`}
          disabled={!hasNext || loading}
          onClick={() => setPage(p => p + 1)}
        >
          Вперед
        </button>
      </div>
    </div>
  );
};
