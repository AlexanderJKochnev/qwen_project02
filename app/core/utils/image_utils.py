import os
import uuid
# from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.core.config.project_config import settings
import io
from PIL import Image, ImageOps
from rembg import remove, new_session  # pip install rembg
from loguru import logger


try:
    SESSION = new_session("u2net")
    logger.info("Сессия rembg успешно инициализирована локально.")
except Exception as e:
    logger.error(f"Не удалось загрузить модель rembg: {e}")
    SESSION = None


def image_aligning(content: bytes):
    max_width = settings.IMAGE_WIDTH
    max_height = settings.IMAGE_HEIGH
    MAX_FILE_SIZE = 100 * 1024
    MARGIN_PERCENT = 0.05  # 5% от размера объекта

    try:
        image = Image.open(io.BytesIO(content))

        # 1. Удаление фона
        if SESSION:
            image = remove(image, session=SESSION).convert("RGBA")

        # 2. Умная обрезка с процентным отступом
        bbox = image.getbbox()
        if bbox:
            obj_w = bbox[2] - bbox[0]
            obj_h = bbox[3] - bbox[1]

            # Считаем отступ на основе самого длинного измерения объекта
            margin = int(max(obj_w, obj_h) * MARGIN_PERCENT)

            # Расширяем рамку с учетом границ холста
            left = max(0, bbox[0] - margin)
            upper = max(0, bbox[1] - margin)
            right = min(image.width, bbox[2] + margin)
            lower = min(image.height, bbox[3] + margin)

            image = image.crop((left, upper, right, lower))

        # 3. Ресайз (сохранение пропорций)
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # 4. Оптимизация до 100 КБ
        attempt = 0
        while attempt < 5:
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG', optimize=True)
            output_data = img_byte_arr.getvalue()

            if len(output_data) <= MAX_FILE_SIZE:
                return output_data

            # Если не влезли, уменьшаем разрешение
            new_size = tuple(int(dim * 0.8) for dim in image.size)
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            attempt += 1

        return output_data

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return content


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
