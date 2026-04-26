// src/forms/fields/ImageGalleryField.ts
import { h } from 'preact';
import { useState, useEffect, useRef } from 'preact/hooks';
import { BaseField, FieldConfig } from './BaseField';
import { IMAGE_BASE_URL } from '../../config/api'; // Используем ваш базовый URL
import { getAuthToken } from '../../lib/apiClient'; // Импортируем получение токена

export interface ImageGalleryConfig extends FieldConfig {
  maxImages?: number;
  recordId: number;
  imageId?: string | null; // Передаем текущий ID картинки из image_id
}

interface ImageItem {
  id: string | number;
  file?: File; // Для новых не сохраненных файлов
  isExisting: boolean;
  order?: number; // Для будущего "один ко многим"
}

export class ImageGalleryField extends BaseField<ImageItem[]> {
  private maxImages: number;
  private recordId: number;
  private imageId: string | null;

  constructor(config: ImageGalleryConfig, value: any, onChange: (name: string, value: any) => void) {
    let normalizedValue: ImageItem[] = [];

    // 1. Если бэкенд прислал массив картинок (будущее один ко многим)
    if (Array.isArray(value) && value.length > 0) {
      normalizedValue = value;
    }
    // 2. Если пока работает старая схема 1-к-1 и есть image_id
    else if (config.imageId) {
      normalizedValue = [{ id: config.imageId, isExisting: true, order: 1 }];
    }

    super(config, normalizedValue, onChange);
    this.maxImages = config.maxImages || 5;
    this.recordId = config.recordId;
    this.imageId = config.imageId || null;
  }

  render() {
    return h(GalleryCore, {
      name: this.config.name,
      label: this.config.label,
      value: this.value,
      maxImages: this.maxImages,
      recordId: this.recordId,
      onChange: (val: ImageItem[]) => this.handleChange(val)
    });
  }
}

interface CoreProps {
  name: string;
  label: string;
  value: ImageItem[];
  maxImages: number;
  recordId: number;
  onChange: (value: ImageItem[]) => void;
}

const GalleryCore = ({ name, label, value, maxImages, recordId, onChange }: CoreProps) => {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: any) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newItems: ImageItem[] = [...value];
    for (let i = 0; i < files.length; i++) {
      if (newItems.length >= maxImages) break;
      newItems.push({
        id: `new-${Math.random()}`,
        file: files[i],
        isExisting: false,
        order: newItems.length + 1
      });
    }

    onChange(newItems);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const removeImage = (id: string | number) => {
    onChange(value.filter(img => img.id !== id));
  };

  return h('div', { className: 'mb-4', key: name },
    h('label', { className: 'label' },
      h('span', { className: 'label-text font-medium' }, label)
    ),

    h('div', { className: 'flex flex-wrap gap-4 p-4 border rounded-lg bg-gray-50' },

      // Отображаем картинки через защищенный враппер
      value.map((img) => h(SecureImageWrapper, {
        key: img.id,
        img,
        recordId,
        onRemove: () => removeImage(img.id)
      })),

      // Кнопка добавления нового файла
      value.length < maxImages && h('div', { className: 'w-32 h-32 flex items-center justify-center' },
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

      h('input', {
        ref: fileInputRef,
        type: 'file',
        accept: 'image/*',
        multiple: maxImages > 1,
        onChange: handleFileChange,
        className: 'hidden'
      })
    ),

    h('div', { className: 'text-xs text-gray-400 mt-1' },
      `Selected ${value.length} of ${maxImages} images`
    )
  );
};

// Внутренний компонент для безопасной загрузки картинок через Blob
const SecureImageWrapper = ({ img, recordId, onRemove }: { img: ImageItem, recordId: number, onRemove: () => void }) => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);

  useEffect(() => {
    let currentUrl: string | null = null;

    if (img.isExisting) {
      // 1. СТРУКТУРА ДЛЯ СТАРОЙ СХЕМЫ (1-к-1): берем id картинки как image_id
      // В будущем, когда будет "один ко многим", вы сможете переписать URL на:
      // `${IMAGE_BASE_URL}/mongodb/thumbnails/${recordId}?n=${img.order}`
      const imageUrl = `${IMAGE_BASE_URL}/mongodb/thumbnails/${img.id}`;
      const token = getAuthToken();

      fetch(imageUrl, {
        headers: { 'Authorization': `Bearer ${token || ''}`, 'Accept': 'image/*' }
      })
      .then(res => res.blob())
      .then(blob => {
        currentUrl = URL.createObjectURL(blob);
        setBlobUrl(currentUrl);
      })
      .catch(err => console.error('Failed to load image in gallery:', err));
    } else if (img.file) {
      // 2. ДЛЯ НОВЫХ ФАЙЛОВ: просто читаем локально из памяти браузера
      currentUrl = URL.createObjectURL(img.file);
      setBlobUrl(currentUrl);
    }

    return () => {
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [img.id]);

  return h('div', { className: 'relative w-32 h-32 bg-white border rounded-lg overflow-hidden group shadow-sm' },
    blobUrl ? h('img', {
      src: blobUrl,
      className: 'w-full h-full object-cover'
    }) : h('div', { className: 'w-full h-full flex items-center justify-center text-xs text-gray-400' }, 'Loading...'),

    h('button', {
      type: 'button',
      onClick: onRemove,
      className: 'absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow'
    }, '✕')
  );
};
