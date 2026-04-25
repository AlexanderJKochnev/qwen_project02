// src/forms/fields/LazySelectField.ts
import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import { BaseField, FieldConfig } from './BaseField';

export interface LazySelectConfig extends FieldConfig {
  loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
}

export class LazySelectField extends BaseField<string> {
  private loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;

  constructor(config: LazySelectConfig, value: any, onChange: (name: string, value: any) => void) {
    // Принудительно кастуем в строку, чтобы избежать багов с числами
    const stringValue = (value !== null && value !== undefined) ? String(value) : '';
    super(config, stringValue, onChange);
    this.loadOptions = config.loadOptions;
  }

  private getDisplayName(item: any): string {
    return item.name || item.name_en || item.name_ru || item.name_fr ||
           item.name_es || item.name_it || item.name_de || item.name_zh || '';
  }

  render() {
    return h(LazySelectCore, {
      name: this.config.name,
      label: this.config.label,
      value: this.value || '',
      required: this.config.required,
      loadOptions: this.loadOptions,
      getDisplayName: this.getDisplayName,
      onChange: (val: string) => this.handleChange(val)
    });
  }
}

interface CoreProps {
  name: string;
  label: string;
  value: string;
  required?: boolean;
  loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
  getDisplayName: (item: any) => string;
  onChange: (value: string) => void;
}

const LazySelectCore = ({ name, label, value, required, loadOptions, getDisplayName, onChange }: CoreProps) => {
  const [options, setOptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isOpen, setIsOpen] = useState(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const searchTimeoutRef = useRef<any>(null);

  // Универсальная функция загрузки (append=true при скролле)
  const load = async (searchTerm: string, pageNum: number, append = false) => {
    setLoading(true);
    try {
      const result = await loadOptions(searchTerm, pageNum);
      const items = result.items || [];

      setHasMore(pageNum * 50 < result.total);
      setOptions(prev => append ? [...prev, ...items] : items);
    } catch (err) {
      console.error('LazySelect load error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Первичная загрузка
  useEffect(() => { load('', 1, false); }, []);

  // Закрытие дропдауна при клике вне элемента
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setSearch(''); // Сбрасываем строку поиска
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Поиск с задержкой (Debounce)
  const handleSearch = (searchTerm: string) => {
    setSearch(searchTerm);
    setPage(1);

    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);

    searchTimeoutRef.current = setTimeout(() => {
      load(searchTerm, 1, false);
    }, 300);
  };

  // Пагинация по скроллу
  const handleScroll = (e: Event) => {
    const target = e.target as HTMLDivElement;
    // Если долистали до низа списка (с запасом 30px)
    const bottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 30;

    if (bottom && hasMore && !loading) {
      const nextPage = page + 1;
      setPage(nextPage);
      load(search, nextPage, true);
    }
  };

  const selectedOption = options.find(opt => String(opt.id) === value);

  return h('div', { className: 'mb-4 relative', ref: containerRef, key: name },
    h('label', { className: 'label' },
      h('span', { className: 'label-text font-medium' },
        label,
        required && h('span', { className: 'text-red-500 ml-1' }, '*')
      )
    ),
    h('div', { className: 'relative' },
      // Имитация селекта через Input
      h('input', {
        type: 'text',
        // Если открыт — показываем то, что ищем. Если закрыт — название выбранного элемента
        value: isOpen ? search : (selectedOption ? getDisplayName(selectedOption) : ''),
        onInput: (e: any) => handleSearch(e.target.value),
        onFocus: () => { setIsOpen(true); setSearch(''); },
        className: 'input input-bordered w-full pr-10 cursor-pointer',
        placeholder: selectedOption ? getDisplayName(selectedOption) : `Search ${label.toLowerCase()}...`,
        required: required && !value
      }),

      // Иконка стрелочки
      h('div', { className: 'absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-gray-400' },
        h('svg', { className: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
          h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', strokeWidth: '2', d: 'M19 9l-7 7-7-7' })
        )
      ),

      // Выпадающий список
      isOpen && h('div', {
        className: 'absolute left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-xl max-h-60 overflow-y-auto z-[1000]',
        onScroll: handleScroll,
        style: { top: '100%' }
      },
        options.map(option => h('div', {
          key: option.id,
          className: `p-3 cursor-pointer hover:bg-gray-100 border-b border-gray-50 last:border-b-0 ${value === String(option.id) ? 'bg-primary text-white hover:bg-primary' : 'text-gray-700'}`,
          onClick: () => {
            onChange(String(option.id));
            setIsOpen(false);
          }
        }, getDisplayName(option))),

        loading && h('div', { className: 'p-3 text-center text-gray-500' }, 'Loading...'),
        !hasMore && options.length > 0 && h('div', { className: 'p-3 text-center text-gray-400 text-sm' }, 'No more items'),
        !loading && options.length === 0 && h('div', { className: 'p-3 text-center text-gray-500' }, 'No results found')
      )
    )
  );
};
