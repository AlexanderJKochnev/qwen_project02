// src/forms/fields/ImageGalleryField.ts
import { h } from 'preact';
import { useState, useRef } from 'preact/hooks';
import { BaseField, FieldConfig } from './BaseField';

export interface ImageGalleryConfig extends FieldConfig {
  maxImages?: number;
  recordId: number; // ID основной записи для формирования URL
}

interface ImageItem {
  id: string | number;
  file?: File; // Для новых не сохраненных файлов
  isExisting: boolean;
}

export class ImageGalleryField extends BaseField<ImageItem[]> {
  private maxImages: number;
  private recordId: number;

  constructor(config: ImageGalleryConfig, value: any, onChange: (name: string, value: any) => void) {
    // Нормализуем входящее значение в массив
    let normalizedValue: ImageItem[] = [];
    if (Array.isArray(value)) {
      normalizedValue = value;
    } else if (value) {
      normalizedValue = [{ id: value, isExisting: true }];
    }

    super(config, normalizedValue, onChange);
    this.maxImages = config.maxImages || 5;
    this.recordId = config.recordId;
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
        isExisting: false
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

    // Сетка изображений
    h('div', { className: 'flex flex-wrap gap-4 p-4 border rounded-lg bg-gray-50' },

      // 1. Отображаем текущие картинки
      value.map((img) => {
        // Если картинка уже есть на сервере — берем ваш эндпоинт thumbnail_png
        // (Для one_to_many сюда можно будет дописывать порядковый номер)
        const imgSrc = img.isExisting
          ? `/api/thumbnail_png/${recordId}`
          : URL.createObjectURL(img.file as File);

        return h('div', { key: img.id, className: 'relative w-32 h-32 bg-white border rounded-lg overflow-hidden group shadow-sm' },
          h('img', {
            src: imgSrc,
            className: 'w-full h-full object-cover',
            // Очищаем URL памяти при размонтировании
            onload: () => { if (!img.isExisting) URL.revokeObjectURL(imgSrc); }
          }),
          // Кнопка удаления
          h('button', {
            type: 'button',
            onClick: () => removeImage(img.id),
            className: 'absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow'
          }, '✕')
        );
      }),

      // 2. Кнопка добавления нового файла (если лимит не исчерпан)
      value.length < maxImages && h('div', {
        className: 'w-32 h-32 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center cursor-pointer hover:border-primary hover:bg-white transition-colors',
        onClick: () => fileInputRef.current?.click()
      },
        h('svg', { className: 'w-8 h-8 text-gray-400', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
          h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', strokeWidth: '2', d: 'M12 4v16m8-8H4' })
        ),
        h('span', { className: 'text-xs text-gray-500 mt-1' }, 'Upload')
      ),

      // Скрытый нативный инпут
      h('input', {
        ref: fileInputRef,
        type: 'file',
        accept: 'image/*',
        multiple: maxImages > 1,
        onChange: handleFileChange,
        className: 'hidden'
      })
    ),

    // Подсказка о количестве
    h('div', { className: 'text-xs text-gray-400 mt-1' },
      `Selected ${value.length} of ${maxImages} images`
    )
  );
};
