// src/forms/fields/LazyCheckboxGroupField.ts
import { h } from 'preact';
import { useState, useEffect, useRef, useMemo } from 'preact/hooks';
import { BaseField, FieldConfig } from './BaseField';

export interface LazyCheckboxConfig extends FieldConfig {
  loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
  // Расширили тип currentValue до any, чтобы прокидывать сложные объекты
  renderExtra?: (id: string, isChecked: boolean, currentValue: any, onChange: (value: any) => void) => h.JSX.Element | null;
}

export class LazyCheckboxGroupField extends BaseField<any[]> {
  private loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
  private renderExtra?: LazyCheckboxConfig['renderExtra'];

  constructor(config: LazyCheckboxConfig, value: any[], onChange: (name: string, value: any) => void) {
    // Гарантируем, что value всегда массив
    super(config, Array.isArray(value) ? value : [], onChange);
    this.loadOptions = config.loadOptions;
    this.renderExtra = config.renderExtra;
  }

  private getDisplayName(item: any): string {
    return item.name || item.name_en || item.name_ru || item.name_fr || '';
  }

  render() {
    return h(LazyCheckboxCore, {
      name: this.config.name,
      label: this.config.label,
      value: this.value,
      loadOptions: this.loadOptions,
      getDisplayName: this.getDisplayName,
      renderExtra: this.renderExtra,
      onChange: (val: any[]) => this.handleChange(val)
    });
  }
}

interface CoreProps {
  name: string;
  label: string;
  value: any[];
  loadOptions: (search: string, page: number) => Promise<{ items: any[], total: number }>;
  getDisplayName: (item: any) => string;
  renderExtra?: LazyCheckboxConfig['renderExtra'];
  onChange: (value: any[]) => void;
}

const LazyCheckboxCore = ({ name, label, value, loadOptions, getDisplayName, renderExtra, onChange }: CoreProps) => {
  const [options, setOptions] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  const load = async (searchTerm: string, pageNum: number, append = false) => {
    setLoading(true);
    try {
      const result = await loadOptions(searchTerm, pageNum);
      setHasMore(pageNum * 20 < result.total);
      setOptions(prev => append ? [...prev, ...result.items] : result.items);
    } catch (err) {
      console.error('LazyCheckbox load error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load('', 1, false); }, []);

  const handleScroll = (e: Event) => {
    const target = e.target as HTMLDivElement;
    const bottom = target.scrollHeight - target.scrollTop <= target.clientHeight + 20;
    if (bottom && hasMore && !loading) {
      const nextPage = page + 1;
      setPage(nextPage);
      load(search, nextPage, true);
    }
  };

  // Метод проверки, выбран ли ID (поддерживает и строки, и объекты с бэкенда)
  const isIdChecked = (id: string) => {
    return value.some(val => {
      if (typeof val === 'object' && val !== null) {
        return String(val.id) === id;
      }
      return String(val) === id;
    });
  };

  const handleToggle = (optionId: string, checked: boolean) => {
    let newValue: any[];

    if (checked) {
      // Если это сложный объект (например, varietals)
      const isObjectMode = value.length > 0 && typeof value[0] === 'object';

      if (isObjectMode || name === 'varietals') {
        newValue = [...value, { id: Number(optionId) }];
      } else if (name === 'foods') {
        newValue = [...value, { id: Number(optionId) }];
      } else {
        newValue = [...value, optionId];
      }
    } else {
      newValue = value.filter(val => {
        if (typeof val === 'object' && val !== null) {
          return String(val.id) !== optionId;
        }
        return String(val) !== optionId;
      });
    }
    onChange(newValue);
  };

  // 🔥 2. СОРТИРОВКА: Выбранные элементы поднимаем наверх
  const sortedOptions = useMemo(() => {
    return [...options].sort((a, b) => {
      const aChecked = isIdChecked(String(a.id));
      const bChecked = isIdChecked(String(b.id));
      if (aChecked && !bChecked) return -1;
      if (!aChecked && bChecked) return 1;
      return 0;
    });
  }, [options, value]);

  return h('div', { className: 'card bg-base-100 shadow mb-4', key: name },
    h('details', {},
      h('summary', { className: 'p-4 font-bold cursor-pointer' }, label),
      h('div', { className: 'border rounded-lg p-2' },
        h('input', {
          type: 'text',
          value: search,
          onInput: (e: any) => {
            setSearch(e.target.value);
            setPage(1);
            load(e.target.value, 1, false);
          },
          className: 'input input-bordered input-sm w-full mb-2',
          placeholder: `Search ${label.toLowerCase()}...`
        }),
        h('div', {
          ref: scrollRef,
          className: 'max-h-60 overflow-y-auto',
          onScroll: handleScroll
        },
          sortedOptions.map(option => {
            const optionId = option.id.toString();
            const isChecked = isIdChecked(optionId);

            return h('div', { key: optionId, className: 'flex items-center mb-2 p-1 hover:bg-gray-50' },
              h('input', {
                type: 'checkbox',
                id: `${name}-${optionId}`,
                checked: isChecked,
                onChange: (e: any) => handleToggle(optionId, e.target.checked),
                className: 'mr-2'
              }),
              h('label', {
                htmlFor: `${name}-${optionId}`,
                className: renderExtra ? 'flex-1 cursor-pointer text-sm' : 'cursor-pointer text-sm'
              }, getDisplayName(option)),
              renderExtra && renderExtra(optionId, isChecked, value, onChange)
            );
          }),
          loading && h('div', { className: 'p-2 text-center text-gray-500 text-sm' }, 'Loading...')
        )
      )
    )
  );
};
