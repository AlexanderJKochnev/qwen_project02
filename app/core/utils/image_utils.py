import os
import uuid
# from pathlib import Path
from typing import Tuple
from fastapi import UploadFile
from app.core.config.project_config import settings
import io
from PIL import Image, ImageOps
from rembg import remove  # pip install rembg


def image_aligning(content):
    width = settings.IMAGE_WIDTH
    height = settings.IMAGE_HEIGH

    try:
        # 1. Открываем изображение
        image = Image.open(io.BytesIO(content))

        # 2. Удаляем фон (интеллектуально)
        # Если нужно сохранить прозрачность, итоговый формат должен быть PNG
        image = remove(image)

        # 3. Умное изменение размера (ImageOps.fit делает кроп под размер с сохранением пропорций)
        # Если нужно просто вписать без обрезки, используйте ImageOps.contain
        image = ImageOps.fit(image, (width, height), Image.Resampling.LANCZOS)

        # 4. Сохранение
        img_byte_arr = io.BytesIO()
        # Если фон удален, лучше сохранять в PNG или конвертировать в RGB перед JPEG
        save_format = 'PNG' if image.mode == 'RGBA' else 'JPEG'
        image.save(img_byte_arr, format=save_format, optimize=True)

        return img_byte_arr.getvalue()

    except Exception as e:
        # Важно: return после raise не сработает. Оставляем что-то одно.
        print(f"Ошибка: {e}")
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
