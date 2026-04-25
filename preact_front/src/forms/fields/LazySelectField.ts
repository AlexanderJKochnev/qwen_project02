// src/forms/fields/LazySelectField.ts
import { h } from 'preact';
import { BaseField, FieldConfig } from './BaseField';

// Интерфейс для расширенной конфигурации
export interface LazySelectConfig extends FieldConfig {
  loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
  pageSize?: number;
}

export class LazySelectField extends BaseField<string> {
  private loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
  private pageSize: number;

  constructor(config: LazySelectConfig, value: string, onChange: (name: string, value: any) => void) {
    super(config, value, onChange);
    this.loadOptions = config.loadOptions;
    this.pageSize = config.pageSize || 50;
  }

  // Метод для вытягивания мультиязычных имен
  private getDisplayName(item: any): string {
    return item.name || item.name_en || item.name_ru || item.name_fr ||
           item.name_es || item.name_it || item.name_de || item.name_zh || '';
  }

  render() {
    // Внутренний компонент для управления загрузкой
    return h(NativeLazySelect, {
      name: this.config.name,
      label: this.config.label,
      value: this.value || '',
      required: this.config.required,
      loadOptions: this.loadOptions,
      onChange: (val: string) => this.handleChange(val)
    });
  }
}

// Внутренний Preact-компонент для обработки хуков (useState, useEffect)
import { useState, useEffect, useRef } from 'preact/hooks';

interface InternalProps {
  name: string;
  label: string;
  value: string;
  required?: boolean;
  loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
  pageSize: number;
  getDisplayName: (item: any) => string;
  onChange: (value: string) => void;
}

const NativeLazySelect = ({ name, label, value, required, loadOptions, onChange }: any) => {
  const [options, setOptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Загружаем только 1 раз при монтировании
  useEffect(() => {
    setLoading(true);
    loadOptions('', 1) // Грузим первую пачку (50 шт)
      .then(result => setOptions(result.items))
      .finally(() => setLoading(false));
  }, []);

  const getDisplayName = (item: any) => {
    return item.name || item.name_en || item.name_ru || '';
  };

  return h('div', { className: 'mb-4', key: name },
    h('label', { className: 'label' },
      h('span', { className: 'label-text font-medium' },
        label,
        required && h('span', { className: 'text-red-500 ml-1' }, '*')
      )
    ),
    // Используем НАСТОЯЩИЙ селект браузера
    h('select', {
      name: name,
      value: value || '',
      onChange: (e: any) => onChange(e.target.value),
      className: 'select select-bordered w-full', // Стили вашей темы
      required: required
    },
      h('option', { value: '' }, loading ? 'Loading...' : `Select ${label.toLowerCase()}`),
      options.map(option =>
        h('option', { key: option.id, value: option.id.toString() }, getDisplayName(option))
      )
    )
  );
};
  useEffect(() => { load('', 1, false); }, []);

  // Закрытие при клике вне селекта
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
        setSearch('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = (searchTerm: string) => {
    setSearch(searchTerm);
    setPage(1);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    searchTimeoutRef.current = setTimeout(() => { load(searchTerm, 1, false); }, 300);
  };

  const handleScroll = (e: Event) => {
    const target = e.target as HTMLDivElement;
    const bottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 50;
    if (bottom && hasMore && !loading) {
      const nextPage = page + 1;
      setPage(nextPage);
      load(search, nextPage, true);
    }
  };

  const selectedOption = options.find(opt => opt.id.toString() === value);

  return h('div', { className: 'mb-4 relative', ref: containerRef, key: name }, // Добавили relative сюда!
    h('label', { className: 'label' },
      h('span', { className: 'label-text' },
        label,
        required && h('span', { className: 'text-red-500 ml-1' }, '*')
      )
    ),
    h('div', { className: 'relative' },
      h('input', {
        type: 'text',
        value: isOpen ? search : (selectedOption ? getDisplayName(selectedOption) : ''),
        onInput: (e: any) => handleSearch(e.target.value),
        onFocus: () => { setIsOpen(true); setSearch(''); },
        className: 'input input-bordered w-full pr-10', // pr-10 освобождает место под стрелку
        placeholder: selectedOption ? getDisplayName(selectedOption) : `Select ${label.toLowerCase()}...`,
        required: required && !value
      }),

      // Иконка стрелочки вниз (SVG)
      h('div', {
        className: 'absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-gray-400'
      },
        h('svg', { className: 'w-5 h-5', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
          h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', strokeWidth: '2', d: 'M19 9l-7 7-7-7' })
        )
      ),
      // Выпадающий список теперь будет строго под инпутом благодаря z-50 и absolute
      isOpen && h('div', {
        className: 'absolute left-0 right-0 z-[100] mt-1 bg-white border border-gray-200 rounded-lg shadow-xl max-h-60 overflow-y-auto',
        onScroll: handleScroll,
        style: { top: '100%' } // Гарантируем появление строго под инпутом
      },
        options.map(option => h('div', {
          key: option.id,
          className: `p-3 cursor-pointer hover:bg-gray-100 border-b border-gray-50 last:border-b-0 ${value === option.id.toString() ? 'bg-primary text-white hover:bg-primary' : 'text-gray-700'}`,
          onClick: () => { onChange(option.id.toString()); setIsOpen(false); }
        }, getDisplayName(option))),

        loading && h('div', { className: 'p-3 text-center text-gray-500' }, 'Loading...'),
        !hasMore && options.length > 0 && h('div', { className: 'p-3 text-center text-gray-400 text-sm' }, 'No more items')
      )
    )
  );
};
