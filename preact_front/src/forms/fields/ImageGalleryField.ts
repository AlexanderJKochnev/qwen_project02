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
  order?: number; // Порядковый номер для будущего many-to-many
}

export class ImageGalleryField extends BaseField<ImageItem[]> {
  private maxImages: number;
  private recordId: number;

  constructor(config: ImageGalleryConfig, value: any, onChange: (name: string, value: any) => void) {
    // Нормализуем входящее значение в массив
    let normalizedValue: ImageItem[] = [];
    if (Array.isArray(value)) {
      normalizedValue = value.map((v, index) => ({
        ...v,
        order: v.order || index + 1
      }));
    } else if (value) {
      normalizedValue = [{ id: value, isExisting: true, order: 1 }];
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

    // Сетка изображений
    h('div', { className: 'flex flex-wrap gap-4 p-4 border rounded-lg bg-gray-50' },

      // 1. Отображаем текущие картинки
      value.map((img) => {
        // Формируем URL. Пока это один ко многим не готов,
        // URL будет просто /api/thumbnail/{id}.
        // Как только бэкенд будет готов к массиву, вы сможете раскомментировать order ниже!
        // отладка
        const fullUrl = `/api/thumbnail/${recordId}`;
        console.log(`[ImageGallery] Requesting image from: ${fullUrl}`);
        const imgSrc = img.isExisting
          ? fullUrl
          : URL.createObjectURL(img.file as File);

        // const imgSrc = img.isExisting
        //  ? `/api/thumbnail/${recordId}` // или `/api/thumbnails/${recordId}?n=${img.order}`
        //  : URL.createObjectURL(img.file as File);

        return h('div', { key: img.id, className: 'relative w-32 h-32 bg-white border rounded-lg overflow-hidden group shadow-sm' },
          h('img', {
            src: imgSrc,
            className: 'w-full h-full object-cover',
            onload: () => { if (!img.isExisting) URL.revokeObjectURL(imgSrc); }
          }),
          // Кнопка удаления поверх превью
          h('button', {
            type: 'button',
            onClick: () => removeImage(img.id),
            className: 'absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow'
          }, '✕')
        );
      }),

      // 2. Кнопка добавления нового файла в виде аккуратной прямоугольной кнопки
      value.length < maxImages && h('div', {
        className: 'w-32 h-32 flex items-center justify-center'
      },
        h('button', {
          type: 'button',
          onClick: () => fileInputRef.current?.click(),
          className: 'btn btn-outline btn-primary btn-sm flex items-center gap-1'
        },
          // Красивая иконка плюса
          h('svg', { className: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' },
            h('path', { strokeLinecap: 'round', strokeLinejoin: 'round', strokeWidth: '2', d: 'M12 4v16m8-8H4' })
          ),
          h('span', {}, 'Add')
        )
      ),

      // Скрытый нативный инпут для вызова диалогового окна ОС
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
