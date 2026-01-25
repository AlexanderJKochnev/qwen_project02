# app/mongodb/migration.py
import asyncio
from fastapi import Depends
import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
# from app.core.config.project_config import settings
from app.mongodb.repository import ThumbnailImageRepository
from app.core.config.database.db_mongo import get_mongodb
# from app.mongodb.config import settings
from app.core.config.project_config import settings


async def get_migration_database():
    """Создает прямое подключение к MongoDB для миграции"""
    #  client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongo_url)
    #  return client[settings.MONGODB_DB]

    try:
        client = AsyncIOMotorClient(settings.mongo_url, serverSelectionTimeoutMS=5000)
        await client.admin.command('ping')
        print("MongoDB connection good")
        return client[settings.MONGO_DATABASE]
        # client.close()
        # return True
    except Exception as e:
        print(f"MongoDB connection failed: {e}")


async def migrate_existing_images():  # database: AsyncIOMotorDatabase = get_database):
    """Миграция существующих изображений - добавление thumbnail'ов"""
    try:
        db = await get_migration_database()
        # db = await database()
        repository = ThumbnailImageRepository(db)

        print("Starting image migration...")

        # Получаем все изображения без thumbnail'ов
        images = await repository.get_all_images_without_thumbnail()
        print(f"Found {len(images)} images without thumbnails")

        success_count = 0
        error_count = 0

        for image in images:
            try:
                print(f"Processing image: {image['filename']}")

                # Создаем thumbnail
                thumbnail_content = repository._create_thumbnail_png(image["content"])

                if thumbnail_content:
                    # Обновляем документ
                    updated = await repository.update_image_with_thumbnail(
                        image["_id"], thumbnail_content
                    )

                    if updated:
                        success_count += 1
                        print(f"✓ Added thumbnail for {image['filename']}")
                    else:
                        error_count += 1
                        print(f"✗ Failed to update {image['filename']}")
                else:
                    error_count += 1
                    print(f"✗ Failed to create thumbnail for {image['filename']}")

            except Exception as e:
                error_count += 1
                print(f"✗ Error processing {image['filename']}: {e}")

        print(f"Migration completed: {success_count} successful, {error_count} errors")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        # Закрываем подключение
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    asyncio.run(migrate_existing_images())
    # asyncio.run(get_migration_database())
