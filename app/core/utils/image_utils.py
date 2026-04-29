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


def image_aligning(content: bytes):
    try:
        logger.info(f"Начало обработки. Размер входящих данных: {len(content)} байт")
        
        # 1. Загрузка
        image = Image.open(io.BytesIO(content))
        logger.info(f"Изображение открыто. Размер: {image.size}, Режим: {image.mode}")
        
        # 2. Удаление фона
        # session лучше вынести в глобальную область, чтобы не загружать модель каждый раз
        session = new_session("u2net")
        result = remove(image, session = session)
        
        # ПРОВЕРКА: появился ли альфа-канал и есть ли в нем прозрачные пиксели
        if result.mode != 'RGBA':
            logger.warning("ВНИМАНИЕ: rembg не вернул RGBA режим. Фон точно не удален.")
        else:
            extrema = result.getextrema()
            alpha_min = extrema[3][0]  # Минимальное значение в альфа-канале
            logger.info(f"Альфа-канал проверен. Минимальное значение (0-прозрачно): {alpha_min}")
            if alpha_min == 255:
                logger.warning("Альфа-канал полностью залит (нет прозрачных зон).")
        
        # 3. Ресайз
        target_size = (settings.IMAGE_WIDTH, settings.IMAGE_HEIGH)
        result = ImageOps.fit(result, target_size, Image.Resampling.LANCZOS)
        logger.info(f"Ресайз до {target_size} выполнен.")
        
        # 4. Сохранение
        img_byte_arr = io.BytesIO()
        result.save(img_byte_arr, format = 'PNG')
        output_data = img_byte_arr.getvalue()
        
        logger.info(f"Обработка завершена успешно. Итоговый размер: {len(output_data)} байт")
        return output_data
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info = True)
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
