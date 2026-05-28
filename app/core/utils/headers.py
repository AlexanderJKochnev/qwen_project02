# app.core.utils.headers.py
"""
    генераторы заголовков для картинок
"""
import struct
from loguru import logger


def generate_image_headers(image_bytes: bytes, **kwargs) -> dict:
    """
        генератор заголовков для файлов
        **kwargs кастомные записи для заголовка (id файла)
    """
    file_size = len(image_bytes)
    if file_size < 24:
        return {"Content-Length": str(file_size), "Content-Type": "application/octet-stream"}

    # Определение формата по сигнатуре (магическим байтам)
    if image_bytes.startswith(b'\xff\xd8\xff'):
        content_type = "image/jpeg"
        width, height = _get_jpeg_size(image_bytes)
    elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        content_type = "image/png"
        width, height = _get_png_size(image_bytes)
    elif image_bytes.startswith(b'RIFF') and image_bytes[8:12] == b'WEBP':
        content_type = "image/webp"
        width, height = _get_webp_size(image_bytes)
    elif image_bytes.startswith((b'GIF87a', b'GIF89a')):
        content_type = "image/gif"
        width, height = struct.unpack('<HH', image_bytes[6:10])
    else:
        # Фоллбек для неопознанных форматов
        return {
            "Content-Length": str(file_size),
            "Content-Type": "application/octet-stream"
        }

    # Сборка стандартных и кастомных мета-заголовков
    headers = {
        "Content-Type": content_type,
        "Content-Length": str(file_size),
        # "Cache-Control": "public, max-age=31536000, immutable",  # Для оптимизации загрузки с 2020+
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",  # only for test
        "Pragma": "no-cache",  # only for test
        "Accept-Ranges": "bytes",
        "X-Original-File-Size": str(file_size)
    }
    if kwargs:
        x_headers = {f'X-{key.lower().replace(' ', '-')}': str(val) for key, val in kwargs.items()}
        headers.update(x_headers)
    # Если размеры успешно определены, добавляем их
    if width and height:
        headers["X-Image-Width"] = str(width)
        headers["X-Image-Height"] = str(height)
        headers["Content-Disposition"] = f'inline; filename="image.{content_type.split("/")[1]}"'

    return headers

# --- Вспомогательные функции разбора байт ---


def _get_png_size(data):
    # Размеры лежат в чанке IHDR (байты 16-24)
    return struct.unpack('>II', data[16:24])


def _get_gif_size(data):
    return struct.unpack('<HH', data[6:10])


def _get_webp_size(data):
    vp8_type = data[12:16]
    if vp8_type == b'VP8 ' and len(data) >= 30:
        # Простой WebP без альфа-канала
        w, h = struct.unpack('<HH', data[26:30])
        return w & 0x3fff, h & 0x3fff
    elif vp8_type == b'VP8X' and len(data) >= 30:
        # Расширенный WebP (с альфа-каналом или анимацией)
        # Размеры кодируются 3 байтами (24 бита)
        w = int.from_bytes(data[24:27], 'little') + 1
        h = int.from_bytes(data[27:30], 'little') + 1
        return w, h
    elif vp8_type == b'VP8L' and len(data) >= 25:
        # Lossless WebP
        b1, b2, b3, b4 = data[21:25]
        w = 1 + (((b2 & 0x3f) << 8) | b1)
        h = 1 + (((b4 & 0xf) << 10) | (b3 << 2) | ((b2 & 0xc0) >> 6))
        return w, h
    return None, None


def _get_jpeg_size(data):
    # Парсинг JPEG маркеров SOF0-SOF3
    idx = 2
    while idx < len(data):
        if data[idx] == 0xFF:
            marker = data[idx + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3):  # Маркеры начала кадра (SOF)
                # Размеры находятся после длины сегмента (2 байта) и точности (1 байт)
                h, w = struct.unpack('>HH', data[idx + 5:idx + 9])
                return w, h
            elif marker == 0xD9:  # Конец изображения
                break
            else:
                # Пропускаем текущий сегмент
                idx += 2 + int.from_bytes(data[idx + 2:idx + 4], 'big')
        else:
            idx += 1
    return None, None


def make_meta(fid: str, fid_thumb: str, full_data: bytes, thumb_data: bytes, description: str,
              data_hash: int,
              table_name: str,
              mime_type: str):
    """
    make meta for seawwed images for clickhouse records
    """
    return {'fid': fid,
            'fid_thumb': fid_thumb,
            'size_bytes': len(full_data),
            'thumb_size_bytes': len(thumb_data),
            'tags': description,
            'data_hash': data_hash,
            'table': table_name,
            'mime_type': mime_type
            }


def content_type_magic(image_bytes: bytes):
    # Определение формата по сигнатуре (магическим байтам)
    if image_bytes.startswith(b'\xff\xd8\xff'):
        content_type = "image/jpeg"
        width, height = _get_jpeg_size(image_bytes)
    elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        content_type = "image/png"
        width, height = _get_png_size(image_bytes)
    elif image_bytes.startswith(b'RIFF') and image_bytes[8:12] == b'WEBP':
        content_type = "image/webp"
        width, height = _get_webp_size(image_bytes)
    elif image_bytes.startswith((b'GIF87a', b'GIF89a')):
        content_type = "image/gif"
        width, height = struct.unpack('<HH', image_bytes[6:10])
    else:
        content_type = "application/octet-stream"
        width, height = 0, 0
        # Фоллбек для неопознанных форматов
    return content_type, width, height
