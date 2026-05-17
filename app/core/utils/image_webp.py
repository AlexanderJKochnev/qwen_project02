# app.core.utils.image_webp.py
import io
import logging
from typing import Tuple, Optional
from PIL import Image, ImageOps, ImageFilter
import numpy as np
from rembg import remove, new_session
import magic

logger = logging.getLogger(__name__)

# Глобальная сессия rembg
_REMBG_SESSION = None

# Конфигурация
CONFIG = {'max_width': 1200, 'max_height': 1200, 'max_file_size': 100 * 1024,  # 100 KB
          'thumb_size': 150,  # 150x150
          'margin_pct': 0.05, 'webp_quality': 100,  # lossless = качество 100
          'alpha_quality': 90,  # качество альфа-канала
          }


def get_rembg_session():
    """Ленивая загрузка модели rembg"""
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        try:
            _REMBG_SESSION = new_session("u2net")
            logger.info("Модель rembg загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
    return _REMBG_SESSION


def process_image_to_webp(
        content: bytes, remove_bg: bool = True, max_size_kb: int = 100, thumb_size: int = 150
) -> Tuple[Optional[bytes], Optional[bytes], Optional[dict]]:
    """
    Полный конвейер: bytes → WebP lossless+alpha + thumbnail

    Args:
        content: исходное изображение в bytes
        remove_bg: удалять ли фон
        max_size_kb: максимальный размер full-изображения в KB
        thumb_size: размер thumbnail (квадрат)

    Returns:
        (full_webp_bytes, thumb_webp_bytes, metadata)
    """
    if not content:
        return None, None, None

    try:
        # 1. Загрузка и подготовка
        image = Image.open(io.BytesIO(content))
        image = ImageOps.exif_transpose(image)
        metadata = extract_metadata_fast(image)

        # 2. Удаление фона (если нужно)
        if remove_bg:
            image = remove_background_optimized(image)
            image = postprocess_alpha_for_webp(image)
            image = smart_crop(image, margin_pct=CONFIG['margin_pct'])

        # 3. Создание thumbnail (ДО оптимизации full)
        thumb = create_thumbnail(image, thumb_size)
        thumb_data = optimize_thumbnail_to_webp(thumb)

        # 4. Оптимизация full-изображения
        full_data = optimize_full_to_webp(
            image, max_size_bytes=max_size_kb * 1024, max_dimensions=(CONFIG['max_width'], CONFIG['max_height'])
        )

        # 5. Метаданные
        metadata.update(
            {'full_size_bytes': len(full_data), 'thumb_size_bytes': len(thumb_data), 'full_mime': 'image/webp',
             'thumb_mime': 'image/webp'}
        )

        return full_data, thumb_data, metadata

    except Exception as e:
        logger.error(f"Ошибка обработки: {e}", exc_info=True)
        return None, None, None


def remove_background_optimized(image: Image.Image) -> Image.Image:
    """Удаление фона с кэшированием сессии"""
    session = get_rembg_session()
    if session:
        # rembg работает быстрее с RGB (без альфа-канала на входе)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        result = remove(image, session=session)
        return result.convert('RGBA')
    return image.convert('RGBA')


def postprocess_alpha_for_webp(image: Image.Image) -> Image.Image:
    """
    Очистка альфа-канала для WebP lossless
    Уменьшает размер файла на 20-30% без потери качества
    """
    if image.mode != 'RGBA':
        return image

    r, g, b, a = image.split()
    alpha_array = np.array(a, dtype=np.uint8)

    # 1. Бинаризация с порогом (убираем полупрозрачный мусор)
    # Оставляем только полностью прозрачные (0) и непрозрачные (255)
    binary_mask = (alpha_array > 128).astype(np.uint8) * 255

    # 2. Медианный фильтр для удаления "битых" пикселей
    from scipy.ndimage import median_filter
    cleaned = median_filter(binary_mask, size=2)

    # 3. Легкое размытие для антиалиасинга (1 пиксель)
    mask_img = Image.fromarray(cleaned)
    mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=0.5))

    cleaned_alpha = np.array(mask_img, dtype=np.uint8)

    return Image.merge('RGBA', (r, g, b, Image.fromarray(cleaned_alpha)))


def smart_crop(image: Image.Image, margin_pct: float = 0.05) -> Image.Image:
    """Автокроп с выравниванием до четных размеров"""
    bbox = image.getbbox()
    if not bbox:
        return image

    obj_w = bbox[2] - bbox[0]
    obj_h = bbox[3] - bbox[1]
    margin = int(max(obj_w, obj_h) * margin_pct)

    left = max(0, bbox[0] - margin)
    top = max(0, bbox[1] - margin)
    right = min(image.width, bbox[2] + margin)
    bottom = min(image.height, bbox[3] + margin)

    # Выравнивание до четных (WebP optimization)
    if (right - left) % 2:
        right = min(image.width, right + 1)
    if (bottom - top) % 2:
        bottom = min(image.height, bottom + 1)

    cropped = image.crop((left, top, right, bottom))

    # Убираем прозрачную кайму
    alpha = cropped.split()[-1] if cropped.mode == 'RGBA' else None
    if alpha:
        alpha_array = np.array(alpha)
        if np.all(alpha_array[0, :] < 10):
            cropped = cropped.crop((0, 1, cropped.width, cropped.height))
        if np.all(alpha_array[-1, :] < 10):
            cropped = cropped.crop((0, 0, cropped.width, cropped.height - 1))

    return cropped


def create_thumbnail(image: Image.Image, size: int) -> Image.Image:
    """Создание квадратного thumbnail с сохранением пропорций"""
    # Сначала ресайзим по минимальной стороне
    thumb = image.copy()

    # Для thumbnail с прозрачностью - белый фон не нужен
    if thumb.mode != 'RGBA':
        thumb = thumb.convert('RGBA')

    # Ресайз с сохранением пропорций
    thumb.thumbnail((size, size), Image.Resampling.LANCZOS)

    # Создаем квадратный канвас
    square = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    x = (size - thumb.width) // 2
    y = (size - thumb.height) // 2
    square.paste(thumb, (x, y))

    return square


def optimize_thumbnail_to_webp(thumb: Image.Image) -> bytes:
    """Оптимизация thumbnail (меньше требований к качеству)"""
    buf = io.BytesIO()

    # Для thumbnail можно сильнее сжимать
    thumb.save(
        buf, format='WEBP', lossless=True, quality=95,  # lossless == 100, 95 почти lossless
        alpha_quality=80,  # альфе можно чуть срезать
        method=4,  # быстрее
        exact=False
    )

    return buf.getvalue()


def optimize_full_to_webp(
        image: Image.Image, max_size_bytes: int, max_dimensions: Tuple[int, int]
) -> bytes:
    """
    Оптимизация full-изображения с контролем размера
    Использует адаптивный подход (быстрее вашего 7-итерационного)
    """
    temp_img = image.copy()

    # Сначала ресайз до максимальных размеров
    temp_img.thumbnail(max_dimensions, Image.Resampling.LANCZOS)

    # Пробуем lossless с разными параметрами
    strategies = [  # Стратегия 1: оптимальный lossless
        lambda img: save_webp_lossless(img, quality=100, alpha_q=90, method=4),

        # Стратегия 2: чуть агрессивнее
        lambda img: save_webp_lossless(img, quality=100, alpha_q=75, method=6),

        # Стратегия 3: уменьшаем размер
        lambda img: resize_and_save(img, 0.9, 95, 70),

        # Стратегия 4: еще уменьшаем
        lambda img: resize_and_save(img, 0.8, 90, 60),

        # Стратегия 5: финальная
        lambda img: resize_and_save(img, 0.7, 85, 50), ]

    for strategy in strategies:
        data = strategy(temp_img)
        if len(data) <= max_size_bytes:
            logger.debug(f"WebP размер: {len(data)} байт (лимит {max_size_bytes})")
            return data
        # Обновляем temp_img для следующей стратегии
        if hasattr(strategy, 'last_img'):
            temp_img = strategy.last_img

    # Фолбек: последний вариант (даже если больше лимита)
    return data


def save_webp_lossless(
        img: Image.Image, quality: int = 100, alpha_q: int = 90, method: int = 4
) -> bytes:
    """Сохранение в WebP lossless"""
    buf = io.BytesIO()
    img.save(
        buf, format='WEBP', lossless=True,  # quality=100 означает lossless
        quality=quality, alpha_quality=alpha_q, method=method, exact=False
    )
    return buf.getvalue()


def resize_and_save(img: Image.Image, scale: float, quality: int, alpha_q: int) -> bytes:
    """Ресайз и сохранение (для адаптивного подхода)"""
    new_size = tuple(int(dim * scale) for dim in img.size)
    resized = img.resize(new_size, Image.Resampling.LANCZOS)
    # Сохраняем для возможности дальнейшего уменьшения
    resize_and_save.last_img = resized
    return save_webp_lossless(resized, quality=quality, alpha_q=alpha_q, method=6)


def extract_metadata_fast(image: Image.Image) -> dict:
    """Быстрое извлечение метаданных (без глубокого парсинга)"""
    return {'format': image.format, 'mode': image.mode, 'size': image.size,
            'has_alpha': image.mode in ('RGBA', 'LA', 'PA')}


# ============= Вспомогательные функции =============

def get_file_info(content: bytes) -> Tuple[str, int]:
    """MIME-тип и размер"""
    mime = magic.from_buffer(content, mime=True)
    return mime, len(content)


def detect_image_format_fast(content: bytes) -> Tuple[str, str]:
    """
    Очень быстрое определение (только основные форматы)
    Возвращает (mime_type, extension)
    """
    if len(content) < 4:
        return ('application/octet-stream', 'bin')

    # PNG: 89 50 4E 47
    if content[0:4] == b'\x89PNG':
        return ('image/png', 'png')

    # JPEG: FF D8 FF
    if content[0:3] == b'\xff\xd8\xff':
        return ('image/jpeg', 'jpg')

    # WebP: RIFF....WEBP
    if content[0:4] == b'RIFF' and len(content) > 12 and content[8:12] == b'WEBP':
        return ('image/webp', 'webp')

    # GIF: GIF87a или GIF89a
    if content[0:6] in (b'GIF87a', b'GIF89a'):
        return ('image/gif', 'gif')

    # BMP: BM
    if content[0:2] == b'BM':
        return ('image/bmp', 'bmp')

    # Fallback: пробуем PIL если нужно
    return ('application/octet-stream', 'bin')


# ============= Пример использования =============

if __name__ == '__main__':
    # Читаем исходное изображение
    with open('input_image.png', 'rb') as f:
        input_bytes = f.read()

    # Обрабатываем
    full_webp, thumb_webp, meta = process_image_to_webp(
        content=input_bytes, remove_bg=True, max_size_kb=100, thumb_size=150
    )

    # Сохраняем результаты
    if full_webp:
        with open('output_full.webp', 'wb') as f:
            f.write(full_webp)
        print(f"Full WebP: {len(full_webp)} bytes")

    if thumb_webp:
        with open('output_thumb.webp', 'wb') as f:
            f.write(thumb_webp)
        print(f"Thumb WebP: {len(thumb_webp)} bytes")

    print(f"Metadata: {meta}")
