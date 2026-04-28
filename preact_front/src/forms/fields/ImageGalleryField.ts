// src/forms/fields/ImageGalleryField.ts
import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import { BaseField, FieldConfig } from './BaseField';
import { getAuthToken } from '../../lib/apiClient';
import { IMAGE_BASE_URL } from '../../config/api';

export interface ImageGalleryConfig extends FieldConfig {
  recordId: number;
}

// Описываем структуру объекта изображения
interface ImageItem {
  id: string | number;
  file?: File; // Для новых файлов, выбранных с ПК
  isExisting: boolean; // true - если картинка уже на сервере
}

export class ImageGalleryField extends BaseField<ImageItem[]> {
  private recordId: number;

  constructor(config: ImageGalleryConfig, value: any, onChange: (name: string, value: any) => void) {
    let normalizedValue: ImageItem[] = [];

    // Если значение уже есть, используем его, иначе создаем дефолтную заглушку для текущего фото
    if (Array.isArray(value) && value.length > 0) {
      normalizedValue = value;
    } else {
      normalizedValue = [{ id: 'current_main', isExisting: true }];
    }

    super(config, normalizedValue, onChange);
    this.recordId = config.recordId;
  }

  render() {
    return h(GalleryCore, {
      name: this.config.name,
      label: this.config.label,
      value: this.value,
      recordId: this.recordId,
      onChange: (val: ImageItem[]) => this.handleChange(val)
    });
  }
}

interface CoreProps {
  name: string;
  label: string;
  value: ImageItem[];
  recordId: number;
  onChange: (value: ImageItem[]) => void;
}

const GalleryCore = ({ name, label, value, recordId, onChange }: CoreProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ВОЗВРАЩАЕМ ЛОГИКУ ВЫБОРА ФАЙЛА С КОМПЬЮТЕРА
  const handleFileChange = (e: any) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newItems: ImageItem[] = [...value];
    for (let i = 0; i < files.length; i++) {
      newItems.push({
        id: `new-${Math.random()}`,
        file: files[i],
        isExisting: false
      });
    }

    onChange(newItems);
    if (fileInputRef.current) fileInputRef.current.value = ''; // Сброс инпута
  };

  const removeImage = (id: string | number) => {
    onChange(value.filter(img => img.id !== id));
  };

  return h('div', { className: 'mb-4', key: name },
    h('label', { className: 'label' },
      h('span', { className: 'label-text font-medium' }, label)
    ),

    // Контейнер с серой подложкой
    h('div', { className: 'flex flex-wrap gap-4 p-4 border rounded-lg bg-gray-50' },

      // Рендерим все выбранные и текущие картинки
      value.map((img) => h(SecureImageWrapper, {
        key: img.id,
        img,
        recordId,
        onRemove: () => removeImage(img.id)
      })),

      // ВОЗВРАЩАЕМ КНОПКУ ДОБАВЛЕНИЯ КАРТИНКИ
      h('div', { className: 'w-32 h-32 flex items-center justify-center' },
        h('button', {
          type: 'button',
          onClick: () => fileInputRef.current?.click(),
          className: 'btn btn-outline btn-primary btn-sm flex items-center gap-1'
        },
          h('svg', { className: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
            h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', strokeWidth: '2', d: 'M12 4v16m8-8H4' })
          ),
          h('span', {}, 'Add')
        )
      ),

      // Скрытый нативный инпут для импорта
      h('input', {
        ref: fileInputRef,
        type: 'file',
        accept: 'image/*',
        onChange: handleFileChange,
        className: 'hidden'
      })
    )
  );
};

const SecureImageWrapper = ({ img, recordId, onRemove }: { img: ImageItem, recordId: number, onRemove: () => void }) => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(img.isExisting);

  useEffect(() => {
    let currentUrl: string | null = null;
    let isMounted = true;

    if (img.isExisting) {
      // ИСПОЛЬЗУЕМ ВАШ НОВЫЙ ЭНДПОИНТ И АВТОРИЗАЦИЮ
      const imageUrl = `${IMAGE_BASE_URL}/items/thumbnail/${recordId}`;
      const token = getAuthToken();

      const loadImage = async () => {
        try {
          const response = await fetch(imageUrl, {
            headers: {
              'Authorization': `Bearer ${token || ''}`,
              'Accept': 'image/*'
            }
          });

          if (!response.ok) throw new Error(`HTTP ${response.status}`);

          const blob = await response.blob();
          if (isMounted) {
            currentUrl = URL.createObjectURL(blob);
            setBlobUrl(currentUrl);
            setLoading(false);
          }
        } catch (err) {
          console.error('Failed to load secure image:', err);
          if (isMounted) setLoading(false);
        }
      };

      loadImage();
    } else if (img.file) {
      // Для новых файлов делаем превью локально
      currentUrl = URL.createObjectURL(img.file);
      setBlobUrl(currentUrl);
      setLoading(false);
    }

    return () => {
      isMounted = false;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [img.id, recordId]);

  // СТРОГОЕ ОГРАНИЧЕНИЕ РАЗМЕРОВ (исправляет гигантское растягивание)
  return h('div', { className: 'relative w-32 h-32 bg-white border rounded-lg overflow-hidden group shadow-sm flex items-center justify-center' },
    loading
      ? h('span', { className: 'loading loading-spinner loading-md text-primary' })
      : blobUrl
        ? h('img', {
            src: blobUrl,
            className: 'w-full h-full object-contain' // Заполняет квадрат, не ломая пропорции
          })
        : h('div', { className: 'text-xs text-gray-400' }, 'Ошибка'),

    // Кнопка удаления (крестик)
        h('button', {
      type: 'button',
      onClick: (e: MouseEvent) => {
        // 1. ОСТАНАВЛИВАЕМ ВСПОЛЫТИЕ (активируем кнопку, блокируя поведение label)
        e.stopPropagation();
        e.preventDefault();

        // 2. ОБНУЛЯЕМ ПОЛЕ ДЛЯ БЭКЕНДА
        onChange('image_id', null);

        // 3. УДАЛЯЕМ ИЗ ВИЗУАЛЬНОГО СПИСКА
        onRemove();
      },
      className: 'absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow'
    }, '✕')
  );
};
