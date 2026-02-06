# app/mongodb/repository.py
from bson import ObjectId, Binary
from datetime import datetime, timezone
from fastapi import Depends
from typing import List, Tuple, Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from loguru import logger
from app.core.config.database.db_mongo import get_mongodb
from app.mongodb.models import FileResponse  # , ImageResponse

import io
from PIL import Image


class ImageRepository:
    def __init__(self, database: AsyncIOMotorDatabase = Depends(get_mongodb)):
        self.db = database
        self.collection = self.db["images"]
        self._indexes_created = False

    async def ensure_indexes(self):
        """Создает индексы при первом использовании репозитория"""
        if not self._indexes_created:
            await self.collection.create_index([("filename", -1)], unique=True)
            await self.collection.create_index([("created_at", -1)])
            await self.collection.create_index([("filename", "text")])  # Текстовый поиск
            self._indexes_created = True
            # print("Image repository indexes ensured")

    async def create_image(self, filename: str, content: bytes, content_type: str, description: str) -> str:
        """ сохранение изображения в базе данных"""
        await self.ensure_indexes()
        document = {
            "filename": filename,
            "content": content,
            "description": description,
            "created_at": datetime.now(timezone.utc),
            "size": len(content),
            "content_type": content_type
        }
        result = await self.collection.insert_one(document)
        if hasattr(result, 'inserted_id'):
            return str(result.inserted_id)
        else:
            return None

    async def get_image(self, image_id: str):
        """ получение изображени по _id """
        await self.ensure_indexes()
        return await self.collection.find_one({"_id": ObjectId(image_id)})

    async def get_image_by_filename(self, filename: str):
        return await self.collection.find_one({"filename": filename})

    async def get_images_after_date_nopage(self,
                                           after_date: datetime
                                           ) -> List[Tuple]:
        """
            получение списка изображений
            возвращает список кортежей [(image_path, image_id)...]
        """
        await self.ensure_indexes()
        query = {"created_at": {"$gt": after_date}}
        cursor = self.collection.find(query).sort("created_at", -1)
        images = []
        async for image in cursor:
            images.append((image['filename'], str(image["_id"])))
        return images

    async def get_images_after_date(self,
                                    after_date: datetime,
                                    skip: int = 0,
                                    limit: int = 100) -> List[FileResponse]:
        """ получение постраничного списка изображений с деталями"""
        await self.ensure_indexes()
        query = {"created_at": {"$gt": after_date}}
        cursor = self.collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
        images = []
        async for image in cursor:
            image["_id"] = str(image["_id"])
            # images.append(image)
            images.append(FileResponse(**image))
        return images

    async def count_images_after_date(self, after_date: datetime) -> int:
        """
        Подсчитывает количество изображений, созданных после указанной даты
        """
        try:
            query = {"created_at": {"$gt": after_date}}
            return await self.collection.count_documents(query)
        except Exception as e:
            raise Exception(f"Error counting images: {str(e)}")

    async def delete_image(self, image_id: str):
        """ удаление изображения по _id"""
        result = await self.collection.delete_one({"_id": ObjectId(image_id)})
        return result.deleted_count > 0

# ------------thumbnail repo


class ThumbnailImageRepository:
    def __init__(self, database: AsyncIOMotorDatabase = Depends(get_mongodb)):
        self.db = database
        self.collection = self.db["images"]
        self._indexes_created = False
        self.thumbnail_size = (300, 300)  # Размер thumbnail'а

    async def ensure_indexes(self):
        """Создает индексы только если они не существуют"""
        if self._indexes_created:
            return

        try:
            # Получаем информацию о существующих индексах
            existing_indexes = await self.collection.index_information()
            indexes_to_create = []

            # Проверяем какие индексы нужны
            required_indexes = [{"key": [("filename", 1)], "name": "filename_1", "unique": True},
                                {"key": [("created_at", -1), ("_id", 1)], "name": "created_at_-1__id_1"}]

            for required_index in required_indexes:
                index_name = required_index["name"]
                if index_name not in existing_indexes:
                    indexes_to_create.append(required_index)
                    # print(f"Index {index_name} will be created")
                else:
                    pass
                    # print(f"Index {index_name} already exists")
            # Создаем только недостающие индексы
            if indexes_to_create:
                for index_spec in indexes_to_create:
                    # Создаем индекс с указанием фона, чтобы не блокировать коллекцию
                    await self.collection.create_index(
                        index_spec["key"], name=index_spec["name"], unique=index_spec.get("unique", False),
                        background=True  # Важно: создаем в фоне
                    )
                    print(f"✓ Index {index_spec['name']} created successfully")

            self._indexes_created = True
            # print("All indexes are ready")

        except Exception as e:
            print(f"Error ensuring indexes: {e}")

    async def check_indexes_status(self) -> Dict:
        """Проверяет статус всех индексов (для диагностики)"""
        try:
            existing_indexes = await self.collection.index_information()
            return {"total_indexes": len(existing_indexes), "indexes": list(existing_indexes.keys()),
                    "status": "healthy"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _create_thumbnail_png(self, image_content: bytes) -> bytes:
        """Создает thumbnail в формате PNG с сохранением прозрачности"""
        try:
            # Открываем изображение
            image = Image.open(io.BytesIO(image_content))
            # original_size = image.size
            # print(f"Original image size: {original_size}")

            # Вычисляем новые размеры сохраняя пропорции
            max_size = 300
            if image.width > image.height:
                new_width = max_size
                new_height = int((max_size / image.width) * image.height)
            else:
                new_height = max_size
                new_width = int((max_size / image.height) * image.width)

            # print(f"Thumbnail target size: ({new_width}, {new_height})")

            # Ресайзим изображение
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Сохраняем в PNG
            output = io.BytesIO()
            resized_image.save(output, format='PNG', optimize=True)
            result = output.getvalue()

            # print(f"Thumbnail created: {len(result)} bytes (was {len(image_content)} bytes)")
            return result
        except Exception as e:
            print(f"Thumbnail creation error: {e}")
            return None

    async def create_image(self, filename: str, content: bytes, content_type: str, description: str) -> Dict[str, Any]:
        await self.ensure_indexes()

        # Создаем thumbnail
        thumbnail_content = self._create_thumbnail_png(content)

        document = {"filename": filename,
                    "content": Binary(content),  # BinData для MongoDB
                    "thumbnail": Binary(thumbnail_content)
                    if thumbnail_content else None,
                    "description": description,
                    "created_at": datetime.now(timezone.utc), "size": len(content),
                    "thumbnail_size": len(thumbnail_content)
                    if thumbnail_content else 0,
                    "content_type": content_type,
                    "thumbnail_type": "image/png" if thumbnail_content else None,
                    "has_thumbnail": thumbnail_content is not None}

        result = await self.collection.insert_one(document)

        return {"id": str(result.inserted_id), "has_thumbnail": thumbnail_content is not None}

    async def get_image(self, image_id: str, include_content: bool = True) -> Optional[dict]:
        """Получить полноразмерное изображение"""
        await self.ensure_indexes()
        try:
            projection = {"filename": 1, "description": 1,
                          "created_at": 1, "size": 1,
                          "content_type": 1,
                          "thumbnail_size": 1, "has_thumbnail": 1,
                          "thumbnail_type": 1}

            if include_content:
                projection["content"] = 1

            result = await self.collection.find_one(
                {"_id": ObjectId(image_id)}, projection
            )
            if result and "content" in result:
                # Конвертируем Binary обратно в bytes
                result["content"] = result["content"]

            return result
        except Exception as e:
            print(f"Error getting image by ID {image_id}: {e}")
            return None

    async def get_thumbnail(self, image_id: str) -> Optional[dict]:
        """Получить только thumbnail"""
        await self.ensure_indexes()
        try:
            result = await self.collection.find_one(
                {"_id": ObjectId(image_id)}, {"thumbnail": 1, "filename": 1, "thumbnail_type": 1}
            )

            if result and "thumbnail" in result:
                # Конвертируем Binary обратно в bytes
                result["thumbnail"] = result["thumbnail"]

            return result
        except Exception as e:
            print(f"Error getting thumbnail {image_id}: {e}")
            return None

    async def get_thumbnail_by_filename(self, filename: str) -> Optional[dict]:
        """Получить thumbnail по имени файла"""
        await self.ensure_indexes()
        try:
            result = await self.collection.find_one(
                {"filename": filename}, {"thumbnail": 1, "filename": 1, "thumbnail_type": 1}
            )

            if result and "thumbnail" in result:
                result["thumbnail"] = result["thumbnail"]

            return result
        except Exception as e:
            print(f"Error getting thumbnail by filename {filename}: {e}")
            return None

    async def get_images_after_date(
        self, after_date: datetime, skip: int = 0, limit: int = 100
    ) -> List[dict]:
        """Получить список изображений (без content, только метаданные)"""
        await self.ensure_indexes()
        try:
            cursor = (self.collection.find(
                {"created_at": {"$gt": after_date}},
                {"content": 0,  # Исключаем основной контент
                    "thumbnail": 0}).sort("created_at", -1).skip(skip).limit(limit))

            images = []
            async for image in cursor:
                image["_id"] = str(image["_id"])
                images.append(image)
            return images
        except Exception as e:
            print(f"Error getting images after date: {e}")
            return []

    async def get_images_after_date_nopage(self,
                                           after_date: datetime
                                           ) -> List[Tuple]:
        """
            получение списка изображений
            возвращает список кортежей [(image_path, image_id)...]
        """
        await self.ensure_indexes()
        try:
            cursor = (self.collection.find({"created_at": {"$gt": after_date}},
                                           {"content": 0, "thumbnail": 0})).sort("created_at", -1)
            images = []
            async for image in cursor:
                image = (str(image["_id"]), image["filename"])
                images.append(image)
            return images
        except Exception as e:
            logger.error(f"Error getting images after date: {e}")
            raise Exception(f'get_images_after_date_nopage: {e}')

    async def get_id_by_filename(self, filename: str) -> Optional[ObjectId]:
        await self.ensure_indexes()
        projection = {"_id": 1}
        doc = await self.collection.find_one({"filename": filename}, projection)
        return str(doc["_id"]) if doc else None

    async def get_image_by_filename(self, filename: str, include_content: bool = True) -> Optional[dict]:
        await self.ensure_indexes()
        projection = {"filename": 1, "description": 1, "created_at": 1, "size": 1, "content_type": 1,
                      "thumbnail_size": 1, "has_thumbnail": 1, "thumbnail_type": 1}
        if include_content:
            projection["content"] = 1

        result = await self.collection.find_one({"filename": filename}, projection)

        if result and "content" in result:
            result["content"] = result["content"]

        return result

    async def count_images_after_date(self, after_date: datetime) -> int:
        await self.ensure_indexes()
        query = {"created_at": {"$gt": after_date}}
        return await self.collection.count_documents(query)

    async def delete_image(self, image_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(image_id)})
        return result.deleted_count > 0

    # Методы для миграции
    async def get_all_images_without_thumbnail(self) -> List[dict]:
        """Получить все изображения без thumbnail'ов"""
        cursor = self.collection.find(
            {"has_thumbnail": {"$ne": True}}, {"content": 1, "filename": 1, "content_type": 1}
        )

        images = []
        async for image in cursor:
            if "content" in image:
                image["content"] = image["content"]
                image["_id"] = str(image["_id"])
                images.append(image)
        return images

    async def update_image_with_thumbnail(self, image_id: str, thumbnail_content: bytes) -> bool:
        """Обновить изображение, добавив thumbnail"""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(image_id)}, {
                    "$set": {"thumbnail": Binary(thumbnail_content), "thumbnail_size": len(thumbnail_content),
                             "thumbnail_type": "image/png", "has_thumbnail": True}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating image {image_id}: {e}")
            return False
