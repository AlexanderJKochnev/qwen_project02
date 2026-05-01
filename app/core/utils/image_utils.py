import os
import uuid
# from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.core.config.project_config import settings
import io
import magic
from PIL import Image, ImageOps, ExifTags, IptcImagePlugin, TiffImagePlugin
from rembg import remove, new_session  # это встает только на debian
from loguru import logger

_REMBG_SESSION = None


def get_rembg_session():
    """Ленивая загрузка модели при первом обращении"""
    global _REMBG_SESSION
    if _REMBG_SESSION is None:
        try:
            # rembg сам найдет файл в /root/.u2net/u2net.onnx
            _REMBG_SESSION = new_session("u2net")
            logger.info("Модель rembg успешно загружена в память.")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели: {e}")
    return _REMBG_SESSION


def image_aligning(content: bytes, remove_bg: bool = True) -> tuple:
    """
    Полный цикл: Метаданные -> Удаление фона -> Автокроп -> Ресайз -> Оптимизация
    """
    if not content:
        return content

    max_w, max_h = settings.IMAGE_WIDTH, settings.IMAGE_HEIGH
    MAX_FILE_SIZE = 100 * 1024  # не более 100кб
    MARGIN_PCT = 0.05
    thumb_w, thumb_h = 150, 150

    try:
        # 1. Открываем и фиксируем метаданные
        image = Image.open(io.BytesIO(content))
        # Исправляем ориентацию (чтобы фото не было "на боку")
        image = ImageOps.exif_transpose(image)
        # Извлекаем метаданные (вдруг есть?)
        metadata = extract_metadata(image)

        # 2. Интеллектуальная обработка
        if remove_bg:
            session = get_rembg_session()
            if session:
                image = remove(image, session=session).convert("RGBA")

            # Автокроп по границам объекта
            bbox = image.getbbox()
            if bbox:
                obj_w, obj_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                margin = int(max(obj_w, obj_h) * MARGIN_PCT)
                image = image.crop(
                    (max(0, bbox[0] - margin), max(0, bbox[1] - margin), min(image.width, bbox[2] + margin),
                     min(image.height, bbox[3] + margin))
                )

        # 3. ОПТИМИЗАЦИЯ РАЗМЕРА ИЗОБРАЖЕНИЯ
        # А. Основное изображение (Full)
        full_image = image.copy()
        full_image.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        # Оптимизация Full до 100 КБ
        full_data = _optimize_to_size(full_image, MAX_FILE_SIZE)
        # Б. Thumbnail (для ListView)
        thumb_image = image.copy()
        thumb_image.thumbnail((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        thumb_io = io.BytesIO()
        thumb_image.save(thumb_io, format='PNG', optimize=True)
        thumb_data = thumb_io.getvalue()
        metadata['mime_type'], metadata['size_bytes'] = get_file_info(full_data)
        _, metadata['thumbnail_size_bytes'] = get_file_info(thumb_data)
        # from app.core.utils.common_utils import jprint
        # jprint(metadata)
        return full_data, thumb_data, metadata

    except Exception as e:
        logger.error(f"Критическая ошибка обработки: {e}")
        return None, None, None


def extract_metadata(image: Image.Image) -> dict:
    full_meta = {
        "basic": {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
        },
        "exif": {},
        "gps": {},
        "iptc": {},
        "xmp": {}
    }

    # 1. Извлекаем EXIF и GPS
    exif_data = image.getexif()
    if exif_data:
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            # GPS обычно лежит внутри EXIF под ID 34853
            if tag == "GPSInfo":
                gps_data = {}
                for g_tag_id in value:
                    g_tag = ExifTags.GPSTAGS.get(g_tag_id, g_tag_id)
                    gps_data[g_tag] = value[g_tag_id]
                full_meta["gps"] = gps_data
            else:
                full_meta["exif"][tag] = str(value)

    # 2. Извлекаем IPTC (часто в JPEG/TIFF)
    try:
        iptc = IptcImagePlugin.getiptcinfo(image)
        if iptc:
            for tag, value in iptc.items():
                full_meta["iptc"][str(tag)] = value.decode(errors='ignore')
    except Exception as e:
        logger.error(f'Извлекаем IPTC. {e}')

    # 3. Извлекаем XMP (если есть)
    # if hasattr(image, "getxmp"):
    #     full_meta["xmp"] = image.getxmp()

    return full_meta


def get_file_info(content: bytes):
    """Возвращает MIME-тип и размер в байтах"""
    mime = magic.from_buffer(content, mime=True)
    return mime, len(content)


def _optimize_to_size(img, max_size):
    """Вспомогательный метод сжатия до лимита"""
    temp_img = img.copy()
    for _ in range(7):
        buf = io.BytesIO()
        temp_img.save(buf, format='PNG', optimize=True, compress_level=9)
        data = buf.getvalue()
        if len(data) <= max_size:
            logger.warning(f'{len(data)=} {max_size=}')
            return data
        new_size = tuple(int(dim * 0.8) for dim in temp_img.size)
        temp_img = temp_img.resize(new_size, Image.Resampling.LANCZOS)
    return data


class ImageService:
    """Сервис для работы с изображениями"""

    @staticmethod
    def is_allowed_extension(filename: str) -> bool:
        """Проверить допустимое расширение файла"""
        if not filename:
            return False
        ext = filename.rsplit('.', 1)[-1].lower()
        return ext in settings.allowed_extensions

    @staticmethod
    def is_allowed_size(file_size: int) -> bool:
        """Проверить допустимый размер файла"""
        return file_size <= settings.max_file_size

    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """Сгенерировать уникальное имя файла"""
        ext = original_filename.rsplit('.', 1)[-1].lower()
        unique_name = f"{uuid.uuid4().hex}.{ext}"
        return unique_name

    @staticmethod
    async def save_image(file: UploadFile, subdirectory: str = "") -> Tuple[str, str]:
        """
        Сохранить изображение и вернуть путь к нему
        Возвращает: (относительный путь, полный путь)
        """
        # Генерируем уникальное имя файла
        filename = ImageService.generate_unique_filename(file.filename)

        # Создаем путь для сохранения
        if subdirectory:
            relative_path = os.path.join(subdirectory, filename)
        else:
            relative_path = filename

        full_path = os.path.join(settings.UPLOAD_DIR, relative_path)

        # Создаем директории если их нет
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        # Сохраняем файл
        contents = await file.read()
        with open(full_path, "wb") as f:
            f.write(contents)

        return relative_path, full_path

    @staticmethod
    async def process_and_save_image(file: UploadFile, max_width: int = 1920, max_height: int = 1080) -> str:
        """
        Обработать и сохранить изображение с оптимизацией размера
        Возвращает относительный путь к файлу
        """
        # Читаем содержимое файла
        contents = await file.read()
        await file.seek(0)  # Сбрасываем указатель файла

        try:
            # Открываем изображение
            image = Image.open(io.BytesIO(contents))

            # Изменяем размер если нужно
            if image.width > max_width or image.height > max_height:
                image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Генерируем уникальное имя
            filename = ImageService.generate_unique_filename(file.filename or "image.jpg")
            full_path = os.path.join(settings.UPLOAD_DIR, filename)

            # Сохраняем изображение
            if image.mode in ('RGBA', 'LA', 'P'):
                # Если есть прозрачность, сохраняем как PNG
                image = image.convert('RGB')
                filename = filename.rsplit('.', 1)[0] + '.jpg'
                full_path = os.path.join(settings.UPLOAD_DIR, filename)

            image.save(full_path, 'JPEG', quality=85, optimize=True)

            return filename

        except Exception:
            # Если не удалось обработать как изображение, сохраняем как есть
            filename = ImageService.generate_unique_filename(file.filename or "image.jpg")
            full_path = os.path.join(settings.UPLOAD_DIR, filename)
            with open(full_path, "wb") as f:
                f.write(contents)
            return filename

    @staticmethod
    def delete_image(image_path: str) -> bool:
        """Удалить изображение"""
        if not image_path:
            return False

        full_path = os.path.join(settings.UPLOAD_DIR, image_path)
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception:
            pass
        return False
