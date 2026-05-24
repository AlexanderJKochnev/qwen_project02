# app.core.utils.image_utils2.py
import asyncio
import io
from PIL import Image, ImageOps
from app.core.config.project_config import settings


async def create_thumbnail(image_bytes: bytes) -> bytes:
    """Thumbnail в JPEG (без прозрачности)"""
    loop = asyncio.get_event_loop()
    thumb_width, thumb_height = settings.MAX_THUMB_WIDTH, settings.MAX_THUMB_HEIGHT

    def _load():
        img = Image.open(io.BytesIO(image_bytes))
        img = ImageOps.exif_transpose(img)
        return img

    image = await loop.run_in_executor(None, _load)

    def _create():
        # Конвертируем в RGB с белым фоном
        if image.mode == 'RGBA':
            bg = Image.new('RGB', image.size, (255, 255, 255))
            bg.paste(image, mask=image.split()[-1])
            img = bg
        else:
            img = image.convert('RGB')

        # Ресайз
        img.thumbnail(
            (thumb_width, thumb_height), Image.Resampling.LANCZOS
        )

        # Квадрат
        square = Image.new('RGB', (thumb_width, thumb_height), (255, 255, 255))
        x = (thumb_width - img.width) // 2
        y = (thumb_height - img.height) // 2
        square.paste(img, (x, y))

        buf = io.BytesIO()
        square.save(buf, format='JPEG', quality=85, optimize=True)
        return buf.getvalue()

    return await loop.run_in_executor(None, _create)


def get_mime_type(image_bytes: bytes) -> str:
    """
    получение типа графического файла по первым байтам
    """
    if image_bytes.startswith(b'\xff\xd8\xff'):
        content_type = "image/jpeg"
    elif image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
        content_type = "image/png"
    elif image_bytes.startswith(b'RIFF') and image_bytes[8:12] == b'WEBP':
        content_type = "image/webp"
    elif image_bytes.startswith((b'GIF87a', b'GIF89a')):
        content_type = "image/gif"
    else:
        content_type = "application/octet-stream"
    return content_type