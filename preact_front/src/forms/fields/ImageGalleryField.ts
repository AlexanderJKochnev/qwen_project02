// src/forms/fields/ImageGalleryField.ts
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { BaseField, FieldConfig } from './BaseField';
import { getAuthToken } from '../../lib/apiClient';
import { IMAGE_BASE_URL } from '../../config/api'; // Импортируем базовый URL если он нужен

export interface ImageGalleryConfig extends FieldConfig {
  recordId: number;
}

export class ImageGalleryField extends BaseField<string | null> {
  private recordId: number;

  constructor(config: ImageGalleryConfig, value: any, onChange: (name: string, value: any) => void) {
    super(config, value, onChange);
    this.recordId = config.recordId;
  }

  render() {
    return h(GalleryCore, {
      name: this.config.name,
      label: this.config.label,
      recordId: this.recordId,
    });
  }
}

interface CoreProps {
  name: string;
  label: string;
  recordId: number;
}

const GalleryCore = ({ name, label, recordId }: CoreProps) => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let currentUrl: string | null = null;
    let isMounted = true;

    // ВАШ НОВЫЙ ЭНДПОИНТ
    const imageUrl = `${IMAGE_BASE_URL}/items/thumbnail/${recordId}`;
    const token = getAuthToken();

    const loadImage = async () => {
      try {
        setLoading(true);
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
        console.error('Failed to load image in gallery:', err);
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadImage();

    return () => {
      isMounted = false;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [recordId]);

  return h('div', { className: 'mb-4', key: name },
    h('label', { className: 'label' },
      h('span', { className: 'label-text font-medium' }, label)
    ),

    h('div', { className: 'w-48 h-48 bg-white border rounded-lg overflow-hidden group shadow-sm flex items-center justify-center' },
      loading
        ? h('span', { className: 'loading loading-spinner loading-md text-primary' })
        : blobUrl
          ? h('img', {
              src: blobUrl,
              className: 'w-full h-full object-contain'
            })
          : h('div', { className: 'text-xs text-gray-400' }, 'Изображение отсутствует')
    )
  );
};
