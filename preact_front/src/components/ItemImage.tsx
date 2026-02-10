// src/components/ItemImage.tsx
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { IMAGE_BASE_URL } from '../config/api';
import { getAuthToken } from '../lib/apiClient'; // Импортируем получение токена

interface ItemImageProps {
  image_id?: string | null;
  alt?: string;
  size?: 'small' | 'medium' | 'large';
  isFullMode?: boolean; // Добавляем новый пропс
}

export const ItemImage = ({ image_id, alt = 'Item',
                            size = 'medium',
                            isFullMode = false // По умолчанию false
                            }: ItemImageProps) => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(!!image_id);

  const sizePx = size === 'small' ? 60 : size === 'medium' ? 120 : 240;

  useEffect(() => {
    if (!image_id) return;

    let isMounted = true;
    let currentUrl: string | null = null;

    const loadImage = async () => {
      const token = getAuthToken();

      // ЛОГИКА ВЫБОРА ЭНДПОИНТА:
      // Если размер large -> запрашиваем полноразмерное (images)
      // В остальных случаях -> миниатюру (thumbnails)
      const endpoint = size === 'large' ? 'images' : 'thumbnails';
      const imageUrl = `${IMAGE_BASE_URL}/mongodb/${endpoint}/${image_id}`;

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
        console.error(`Failed to load ${endpoint}:`, err);
        if (isMounted) {
          setLoading(false);
          setBlobUrl(null); // Сбрасываем, чтобы показать заглушку "Нет фото"
        }
      }
    };

    loadImage();

    return () => {
      isMounted = false;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [image_id, size]); // Добавили size в зависимости, если он вдруг изменится на лету

  // Вычисляем стили в зависимости от режима
  const imageStyle = isFullMode
    ? {
        width: 'auto',
        height: 'auto',
        maxWidth: '90vw',  // 90% ширины окна
        maxHeight: '85vh', // 85% высоты окна
        objectFit: 'contain' as const,
      }
    : {
        width: `${sizePx}px`,
        height: size === 'large' ? 'auto' : `${sizePx}px`,
        maxHeight: size === 'large' ? '600px' : `${sizePx}px`,
        objectFit: 'contain' as const,
        borderRadius: '4px',
        border: '1px solid #ddd',
      };

  return (
    <img
      src={blobUrl || ''}
      alt={alt}
      style={imageStyle}
    />
  );
};