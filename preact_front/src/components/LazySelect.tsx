// src/components/LazySelect.tsx
import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';

interface LazySelectProps {
  name: string;
  label: string;
  value: string;
  onChange: (name: string, value: string) => void;
  loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
  required?: boolean;
  pageSize?: number;
}

export const LazySelect = ({
  name,
  label,
  value,
  onChange,
  loadOptions,
  required = false,
  pageSize = 50
}: LazySelectProps) => {
  const [options, setOptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<any>(null);

  const getDisplayName = (item: any) => {
    return item.name || item.name_en || item.name_ru || item.name_fr ||
           item.name_es || item.name_it || item.name_de || item.name_zh || '';
  };

  const load = async (searchTerm: string, pageNum: number, append = false) => {
    setLoading(true);
    try {
      const result = await loadOptions(searchTerm, pageNum);
      const newItems = result.items;
      setTotal(result.total);
      setHasMore(pageNum * pageSize < result.total);

      if (append) {
        setOptions(prev => [...prev, ...newItems]);
      } else {
        setOptions(newItems);
      }
    } catch (err) {
      console.error('Failed to load options:', err);
    } finally {
      setLoading(false);
    }
  };

  // Загружаем начальные опции
  useEffect(() => {
    load('', 1, false);
  }, []);

  // Обработка поиска с debounce
  const handleSearch = (searchTerm: string) => {
    setSearch(searchTerm);
    setPage(1);

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(() => {
      load(searchTerm, 1, false);
    }, 300);
  };

  // Загрузка следующей страницы
  const loadMore = () => {
    if (!loading && hasMore) {
      const nextPage = page + 1;
      setPage(nextPage);
      load(search, nextPage, true);
    }
  };

  // Обработка скролла
  const handleScroll = (e: Event) => {
    const target = e.target as HTMLDivElement;
    const bottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 50;
    if (bottom && hasMore && !loading) {
      loadMore();
    }
  };

  // Выбор значения
  const handleSelect = (selectedId: number) => {
    onChange(name, selectedId.toString());
    setIsOpen(false);
  };

  const selectedOption = options.find(opt => opt.id.toString() === value);

  return h('div', { className: 'mb-4', ref: containerRef },
    h('label', { className: 'label' },
      h('span', { className: 'label-text' },
        label,
        required && h('span', { className: 'text-red-500 ml-1' }, '*')
      )
    ),
    h('div', { className: 'relative' },
      // Поле ввода для поиска и отображения выбранного значения
      h('input', {
        type: 'text',
        value: search || (selectedOption ? getDisplayName(selectedOption) : ''),
        onInput: (e: any) => handleSearch(e.target.value),
        onFocus: () => setIsOpen(true),
        className: 'input input-bordered w-full',
        placeholder: `Search ${label.toLowerCase()}...`,
        required: required && !value
      }),

      // Выпадающий список
      isOpen && h('div', {
        className: 'absolute z-50 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-y-auto',
        onScroll: handleScroll
      },
        loading && options.length === 0 && h('div', { className: 'p-2 text-center text-gray-500' }, 'Loading...'),

        options.map(option => h('div', {
          key: option.id,
          className: `p-2 cursor-pointer hover:bg-gray-100 ${value === option.id.toString() ? 'bg-primary text-white' : ''}`,
          onClick: () => handleSelect(option.id)
        }, getDisplayName(option))),

        loading && options.length > 0 && h('div', { className: 'p-2 text-center text-gray-500' }, 'Loading more...'),

        !hasMore && options.length > 0 && h('div', { className: 'p-2 text-center text-gray-400 text-sm' }, 'No more items'),

        options.length === 0 && !loading && h('div', { className: 'p-2 text-center text-gray-500' }, 'No results found')
      )
    )
  );
};