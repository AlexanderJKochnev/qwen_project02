// src/components/CheckboxGroup.tsx

import { h } from 'preact';

interface CheckboxGroupProps {
  title: string;
  items: Array<{ id: number; name: string }>;
  selectedIds: string[];
  onToggle: (id: string, checked: boolean) => void;
  renderExtra?: (id: string, isChecked: boolean) => h.JSX.Element | null;
}

export const CheckboxGroup = ({ title, items, selectedIds, onToggle, renderExtra }: CheckboxGroupProps) => {
  const getDisplayName = (item: any) => {
    return item.name || item.name_en || item.name_ru || item.name_fr ||
           item.name_es || item.name_it || item.name_de || item.name_zh || '';
  };

  const sortedItems = [...items].sort((a, b) => {
    const aChecked = selectedIds.includes(a.id.toString());
    const bChecked = selectedIds.includes(b.id.toString());
    if (aChecked && !bChecked) return -1;
    if (!aChecked && bChecked) return 1;
    return getDisplayName(a).localeCompare(getDisplayName(b));
  });

  return (
    <details>
      <summary>{title}</summary>
      <div className="border rounded-lg p-2 max-h-40 overflow-y-auto">
        {sortedItems.map(item => {
          const id = item.id.toString();
          const isChecked = selectedIds.includes(id);

          return (
            <div key={id} className="flex items-center mb-2">
              <input
                type="checkbox"
                id={`${title.toLowerCase()}-${id}`}
                name={`${title.toLowerCase()}-${id}`}
                checked={isChecked}
                onChange={(e: any) => onToggle(id, e.target.checked)}
                className="mr-2"
              />
              <label htmlFor={`${title.toLowerCase()}-${id}`} className={renderExtra ? 'flex-1 cursor-pointer' : 'cursor-pointer'}>
                {getDisplayName(item)}
              </label>
              {renderExtra && renderExtra(id, isChecked)}
            </div>
          );
        })}
      </div>
    </details>
  );
};