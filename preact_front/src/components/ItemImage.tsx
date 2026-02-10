// src/components/ItemImage.tsx
import { h } from 'preact';
import { useState, useEffect } from 'preact/hooks';
import { IMAGE_BASE_URL } from '../config/api';
import { getAuthToken } from '../lib/apiClient'; // Импортируем получение токена

interface ItemImageProps {
  image_id?: string | null;
  alt?: string;
  size?: 'small' | 'medium' | 'large';
}

export const ItemImage = ({ image_id, alt = 'Item', size = 'medium' }: ItemImageProps) => {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(!!image_id);

  const sizePx = size === 'small' ? 60 : size === 'medium' ? 120 : 240;

  useEffect(() => {
    if (!image_id) return;

    let isMounted = true;
    let currentUrl: string | null = null;

    const loadImage = async () => {
      const token = getAuthToken();
      const imageUrl = `${IMAGE_BASE_URL}/mongodb/thumbnails/${image_id}`;

      try {
        const response = await fetch(imageUrl, {
          headers: {
            'Authorization': `Bearer ${token || ''}`,
            'Accept': 'image/*'
          }
        });

        if (!response.ok) throw new Error('401 or other error');

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

    return () => {
      isMounted = false;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [image_id]);

  // Заглушка, если нет ID или произошла ошибка загрузки
  if (!image_id || (!loading && !blobUrl)) {
    return (
      <div style={{
        width: `${sizePx}px`, height: `${sizePx}px`,
        backgroundColor: '#f0f0f0', display: 'flex',
        alignItems: 'center', justifyContent: 'center',
        color: '#999', fontSize: '12px',
        borderRadius: '4px', border: '1px solid #ddd',
      }}>
        {loading ? 'Загрузка...' : 'Нет фото'}
      </div>
    );
  }

  return (
    <img
      src={blobUrl || ''}
      alt={alt}
      style={{
        width: `${sizePx}px`,
        height: `${sizePx}px`,
        objectFit: 'contain',
        borderRadius: '4px',
        border: '1px solid #ddd',
        display: blobUrl ? 'block' : 'none'
      }}
    />
  );
};
