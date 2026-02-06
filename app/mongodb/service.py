# app/mongodb/service.py
import asyncio
import io
from datetime import datetime, timezone
from typing import List, Tuple, Optional, Dict, Any
from pathlib import Path
from loguru import logger
# from dateutil.relativedelta import relativedelta
from fastapi import Depends, HTTPException, status, UploadFile
from PIL import Image

# from app.mongodb.config import settings
from app.core.utils.common_utils import delta_data
from app.core.config.project_config import settings
from app.core.utils.io_utils import get_filepath_from_dir
from app.mongodb.models import FileListResponse, FileResponse
# from app.core.memcached_cache import cache_image_memcached
from app.mongodb.repository import ImageRepository, ThumbnailImageRepository
from app.mongodb.utils import (file_name, image_aligning, make_transparent_white_bg, read_image_generator, )

# delta = (datetime.now(timezone.utc) - relativedelta(years=2)).isoformat()
# delta = datetime.now(timezone.utc) - relativedelta(years=100)
delta = delta_data(settings.DATA_DELTA)


class ImageService:
    def __init__(self, image_repository: ImageRepository = Depends()):
        self.image_repository = image_repository

    async def upload_image(self,
                           file: UploadFile,
                           description: str,
                           ):
        """
            Создание одной записи с зависимостями - если в таблице есть зависимости
            они будут рекурсивно найдены в связанных таблицах (или добавлены при отсутсвии),
            кроме того будет добавлено изображение
        """
        try:
            content = await file.read()
            content = make_transparent_white_bg(content)
            content_type = "image/png"
            # content = remove_background_with_mask(content)
            if len(content) > 8 * 1024 * 1024:
                content = image_aligning(content)
            filename = file_name(file.filename, settings.LENGTH_RANDOM_NAME, '.png')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"image aligning fault: {e}"
            )
        _id = await self.image_repository.create_image(filename, content, content_type, description)
        return _id, filename

    async def direct_upload_image(self, limit: int = 3):
        """ прямая загрузка файлов
            из upload_dir
            limit - ограничение на количество загружаемых файлов (в основном для целей тестирования)
        """
        try:
            # upload_dir = settings.UPLOAD_DIR
            lost_images = []  # список потерянных файлов
            image_paths = get_filepath_from_dir()
            n = len(image_paths)
            # запускаем
            for m, upload_file in enumerate(read_image_generator(image_paths)):
                try:
                    content = await upload_file.read()
                    filename = upload_file.filename
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"upload_file fault: {e}"
                    )
                # удаляем фон 3 способа доработать
                try:
                    # content = make_transparent_white_bg(content)
                    # content = remove_background(content)
                    # content = remove_background_with_mask(content)
                    content_type = 'image/png'
                    filename = f"{filename.rsplit('.', 1)[0]}.png"
                except Exception as e:
                    HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f'Удаление фона не получилось для {filename}. {e}. Оставляем без изменения')
                # подгоняем размер
                try:
                    if len(content) > 8 * 1024 * 1024:
                        content = image_aligning(content)
                except Exception as e:
                    HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f'Изменение размера не получилось для {filename}. {e}. Оставляем без изменения'
                    )
                description = f'импортированный файл {datetime.now(timezone.utc)}'

                id = await self.image_repository.create_image(filename, content, content_type, description)
                if not id:
                    lost_images.append(filename)

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"error: {e}"
            )
        result = {'number of images': n + 1,
                  'loaded images': m + 1}
        if lost_images:
            result['lost images': lost_images]
        return result

    async def get_image(self,
                        image_id: str
                        ) -> FileResponse:
        image = await self.image_repository.get_image(image_id)
        if not image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        # if image["drink_id"] != drink_id:
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return image

    async def get_image_by_filename(self, filename: str) -> FileResponse:
        image = await self.image_repository.get_image_by_filename(filename)
        if not image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Image "{filename}" not found')
        return image

    async def delete_image(self,
                           image_id: str,
                           ):
        image = await self.image_repository.get_image(image_id)
        if not image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        return await self.image_repository.delete_image(image_id)

    async def get_images_after_date(
        self, after_date: datetime, page: int = 1, per_page: int = 100
    ) -> FileListResponse:
        """
        Сервисный метод для получения изображений с пагинацией

        Args:
            after_date: Дата для фильтрации
            page: Номер страницы (начинается с 1)
            per_page: Количество элементов на странице

        Returns:
            FileListResponse с изображениями и метаданными
        """
        try:
            # Валидация параметров
            if page < 1:
                page = 1
            per_page = settings.PAGE_DEFAULT
            skip = (page - 1) * per_page
            # Получаем изображения
            images = await self.image_repository.get_images_after_date(
                after_date, skip, per_page
            )
            # Получаем общее количество для пагинации
            total = await self.image_repository.count_images_after_date(after_date)

            # Проверяем, есть ли еще страницы
            has_more = (skip + len(images)) < total

            return FileListResponse(
                images=images, total=total, has_more=has_more
            )

        except Exception as e:
            raise Exception(f"Service error: {str(e)}")

    async def get_recent_images(self, hours: int = 24) -> List[FileResponse]:
        """
            Упрощенный метод для получения изображений за последние N часов
        """
        from datetime import datetime, timedelta

        after_date = datetime.utcnow() - timedelta(hours=hours)
        return await self.image_repository.get_images_after_date(after_date)

    async def get_images_list_after_date(
        self, after_date: datetime = delta
    ) -> Tuple:
        """
            возвращает кортеж кортежей  (image_file_name, image_id)...
        """
        try:
            images = await self.image_repository.get_images_after_date_nopage(
                after_date
            )
            return images
        except Exception as e:
            raise Exception(f"Service error: {str(e)}")


class ThumbnailImageService:
    def __init__(self, repository: ThumbnailImageRepository = Depends()):
        self.image_repository = repository

    # @cache_image_memcached(prefix = 'thumbnail', expire = 3600, key_params = ['file_id'])
    async def get_thumbnail(self, file_id: str) -> dict:
        """Получить thumbnail (для списков) - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            image_data = await self.image_repository.get_thumbnail(file_id)

            if not image_data or "thumbnail" not in image_data:
                # print(f"Thumbnail not found in DB for {file_id}, creating...")
                # Если thumbnail нет в базе, создаем его
                full_image = await self.get_full_image(file_id)
                thumbnail_content = self.image_repository._create_thumbnail_png(full_image["content"])

                if thumbnail_content:
                    # Сохраняем в базу асинхронно
                    asyncio.create_task(
                        self._save_thumbnail_background(file_id, thumbnail_content)
                    )

                    return {"content": thumbnail_content, "filename": f"thumb_{full_image['filename']}",
                            "content_type": "image/png", "from_cache": False}
                else:
                    # Если не удалось создать thumbnail, создаем принудительно
                    print(f"Thumbnail creation failed for {file_id}, using forced resize")
                    forced_thumbnail = await self._create_forced_thumbnail(full_image["content"])
                    return {"content": forced_thumbnail, "filename": f"thumb_forced_{full_image['filename']}",
                            "content_type": "image/png", "from_cache": False}

            # Если thumbnail уже есть в базе
            # print(f"Thumbnail found in DB for {file_id}, size: {len(image_data['thumbnail'])} bytes")
            return {"content": image_data["thumbnail"], "filename": f"thumb_{image_data['filename']}",
                    "content_type": image_data.get("thumbnail_type", "image/png"), "from_cache": False}

        except Exception as e:
            raise HTTPException(status_code=500,
                                detail=f"Thumbnail for {file_id} retrieval failed: {str(e)}")

    # @cache_image_memcached(prefix = 'full_image', expire = 3600, key_params = ['file_id'])
    async def get_full_image(self, file_id: str) -> dict:
        """Получить полноразмерное изображение - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            image_data = await self.image_repository.get_image(file_id, include_content=True)
            if not image_data or "content" not in image_data:
                raise HTTPException(status_code=404, detail="Image not found")

            # print(f"Full image retrieved for {file_id}, size: {len(image_data['content'])} bytes")
            return {"content": image_data["content"], "filename": image_data["filename"],
                    "content_type": image_data.get("content_type", "image/png"), "from_cache": False}
        except Exception as e:
            raise HTTPException(
                status_code=404, detail=f"Error in get_full_image for {file_id}: {e}"
            )

    async def _save_thumbnail_background(self, file_id: str, thumbnail_content: bytes):
        """Фоновая задача для сохранения thumbnail'а"""
        try:
            success = await self.image_repository.update_image_with_thumbnail(file_id, thumbnail_content)
            if success:
                pass
                # print(f"✓ Thumbnail saved to DB for {file_id}")
            else:
                pass
                # print(f"✗ Failed to save thumbnail for {file_id}")
        except Exception as e:
            print(f"✗ Error saving thumbnail for {file_id}: {e}")

    async def _create_forced_thumbnail(self, image_content: bytes) -> bytes:
        """Создает thumbnail принудительно"""
        try:
            # from PIL import Image
            # import io

            image = Image.open(io.BytesIO(image_content))
            image.thumbnail((300, 300), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            image.save(output, format='PNG', optimize=True)
            return output.getvalue()

        except Exception as e:
            print(f"Forced thumbnail creation failed: {e}")
            # Возвращаем оригинал как fallback
            return image_content

    async def upload_image(self,
                           file: UploadFile,
                           description: str,
                           ) -> Dict[str, Any]:
        try:
            content = await file.read()
            # content = make_transparent_white_bg(content)
            content_type = "image/png"
            # content = remove_background_with_mask(content)
            if len(content) > 8 * 1024 * 1024:
                content = image_aligning(content)
            filename = file_name(file.filename, settings.LENGTH_RANDOM_NAME, '.png')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"image aligning fault: {e}"
            )
        result = await self.image_repository.create_image(filename, content, content_type, description)
        result['filename'] = filename
        """
            {"id": str,
             "has_thumbnail": bool,
             "filename": str
             }
        """
        return result

    async def delete_image(self,
                           image_id: str,
                           ):
        """
           удаление одного изображения по _id
        """
        image = await self.image_repository.get_image(image_id)
        if not image:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
        return await self.image_repository.delete_image(image_id)

    async def direct_upload_image(self, limit: int = 3):
        """ прямая загрузка файлов
            из upload_dir
            limit - ограничение на количество загружаемых файлов (в основном для целей тестирования)
            1. get list of images in upload directory
            2. compair with database list and filter new only files
            3. add new only files to database
        """
        try:
            lost_images = []  # список потерянных файлов
            # список подходящих файлов
            image_paths: List[Path] = get_filepath_from_dir()
            # количество подходящих файлов
            n = len(image_paths)
            # получаем списков файлов в базе данных [(_id, filename)]
            current_image_list = await self.image_repository.get_images_after_date_nopage(delta)
            # список уже существующих имен файлов
            current_filenames = [b for a, b in current_image_list]
            image_paths_clear = (path for path in image_paths if path.name not in current_filenames)
            duplicate_images = [path.name for path in image_paths if path.name in current_filenames]
            # список файлов уже существующих в бд
            # запускаем
            for m, upload_file in enumerate(read_image_generator(image_paths_clear)):
                try:
                    content = await upload_file.read()
                    filename = upload_file.filename
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"upload_file fault: {e}"
                    )
                # удаление фона 3 варианта закоммнетировано - доделать
                try:
                    # content = make_transparent_white_bg(content)
                    # content = remove_background(content)
                    # content = remove_background_with_mask(content)
                    content_type = 'image/png'
                    filename = f"{filename.rsplit('.', 1)[0]}.png"
                except Exception as e:
                    HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f'Удаление фона не получилось для {filename}. {e}. Оставляем без изменения')
                # подгоняем размер
                try:
                    if len(content) > 8 * 1024 * 1024:
                        # уменьшениие размера до приемлемого
                        content = image_aligning(content)
                except Exception as e:
                    HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f'Изменение размера не получилось для {filename}. {e}. Оставляем без изменения'
                    )
                description = f'импортированный файл {datetime.now(timezone.utc)}'

                id = await self.image_repository.create_image(filename, content, content_type, description)
                if not id:
                    lost_images.append(filename)
            result = {'number_of_images': n + 1}
            if lost_images:
                result['lost_images'] = tuple(lost_images)
                result['number_of_lost_images'] = len(lost_images)
            if duplicate_images:
                result['duplicate_images'] = duplicate_images
                result['number_of_duplicate_images'] = len(duplicate_images)
            result['loaded_images'] = \
                (result.get('number_of_images',
                            0) - result.get('number_of_lost_images',
                                            0) - result.get('number_of_duplicate_images', 0))

            return result
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"error: {e}"
            )

    async def get_images_after_date(
        self, after_date: datetime, page: int = 1, per_page: int = 100
    ) -> FileListResponse:
        """
        Сервисный метод для получения изображений с пагинацией

        Args:
            after_date: Дата для фильтрации
            page: Номер страницы (начинается с 1)
            per_page: Количество элементов на странице

        Returns:
            FileListResponse с изображениями и метаданными
        """
        try:
            # Валидация параметров
            if page < 1:
                page = 1
            skip = (page - 1) * per_page
            # Получаем изображения
            images = await self.image_repository.get_images_after_date(
                after_date, skip, per_page
            )
            # Получаем общее количество для пагинации
            total = await self.image_repository.count_images_after_date(after_date)

            # Проверяем, есть ли еще страницы
            has_more = (skip + len(images)) < total

            return FileListResponse(
                images=images, total=total, has_more=has_more
            )

        except Exception as e:
            raise Exception(f"Service error: {str(e)}")

    async def get_images_list_after_date(
        self, after_date: datetime = delta
    ) -> List[Tuple]:
        """
            возвращает кортеж кортежей  (image_file_name, image_id)...
        """
        try:
            images = await self.image_repository.get_images_after_date_nopage(
                after_date
            )
            return images
        except Exception as e:
            raise Exception(f"Service error: {str(e)}")

    async def get_thumbnail_by_filename(self, file_name: str) -> dict:
        """Получить thumbnail (для списков) - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            image_data = await self.image_repository.get_thumbnail_by_filename(file_name)
            if not image_data or "thumbnail" not in image_data:
                # print(f"Thumbnail not found in DB for {file_name}, creating...")
                # Если thumbnail нет в базе, создаем его
                full_image = await self.get_full_image_by_filename(file_name)
                thumbnail_content = self.image_repository._create_thumbnail_png(full_image["content"])

                if thumbnail_content:
                    # Сохраняем в базу асинхронно
                    file_id = image_data.get('_id')
                    asyncio.create_task(
                        self._save_thumbnail_background(file_id, thumbnail_content)
                    )

                    return {"content": thumbnail_content, "filename": f"thumb_{full_image['filename']}",
                            "content_type": "image/png", "from_cache": False}
                else:
                    # Если не удалось создать thumbnail, создаем принудительно
                    print(f"Thumbnail creation failed for {file_name}, using forced resize")
                    forced_thumbnail = await self._create_forced_thumbnail(full_image["content"])
                    return {"content": forced_thumbnail, "filename": f"thumb_forced_{full_image['filename']}",
                            "content_type": "image/png", "from_cache": False}

            # Если thumbnail уже есть в базе
            # print(f"Thumbnail found in DB for {file_id}, size: {len(image_data['thumbnail'])} bytes")
            return {"content": image_data["thumbnail"], "filename": f"thumb_{image_data['filename']}",
                    "content_type": image_data.get("thumbnail_type", "image/png"), "from_cache": False}

        except Exception as e:
            raise HTTPException(status_code=500,
                                detail=f"Thumbnail for {file_id} retrieval failed: {str(e)}")

    # @cache_image_memcached(prefix = 'full_image', expire = 3600, key_params = ['file_id'])
    async def get_full_image_by_filename(self, file_name: str) -> dict:
        """Получить полноразмерное изображение - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
        try:
            image_data = await self.image_repository.get_image_by_filename(file_name, include_content=True)
            if not image_data or "content" not in image_data:
                raise HTTPException(status_code=404, detail="Image not found")

            # print(f"Full image retrieved for {file_id}, size: {len(image_data['content'])} bytes")
            return {"content": image_data["content"], "filename": image_data["filename"],
                    "content_type": image_data.get("content_type", "image/png"), "from_cache": False}
        except Exception as e:
            raise HTTPException(status_code=404,
                                detail=f"Error in get_full_image for {file_name}: {e}")

    async def get_id_by_filename(self, filename: str) -> Optional[str]:
        if not filename or not isinstance(filename, str):
            raise ValueError("Filename must be a non-empty string")
        return await self.image_repository.get_id_by_filename(filename)
