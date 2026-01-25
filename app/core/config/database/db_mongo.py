# app/core/config/database/db_amongo.py
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config.project_config import settings


class MongoDBManager:
    client: AsyncIOMotorClient = None

    @classmethod
    async def connect(cls):
        if cls.client is None:
            cls.client = AsyncIOMotorClient(
                host=settings.MONGO_HOSTNAME,
                port=settings.MONGO_OUT_PORT,
                username=settings.MONGO_INITDB_ROOT_USERNAME,
                password=settings.MONGO_INITDB_ROOT_PASSWORD,
                authSource='admin',
                directConnection=True,
                maxPoolSize=settings.MAXPOOLSIZE,  # Увеличено
                minPoolSize=settings.MINPOOLSIZE,
                uuidRepresentation="standard",
                compressors='zstd'
            )
            await cls.client.admin.command("ping")

    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()
            cls.client = None


async def get_mongodb() -> AsyncIOMotorDatabase:
    # Просто возвращаем базу, Motor сам управляет пулом
    if MongoDBManager.client is None:
        raise RuntimeError("MongoDB client is not initialized. Did you forget to call it in lifespan?")
    return MongoDBManager.client[settings.MONGO_DATABASE]

#  ПРИМЕНЕНИЕ
#  mongo_db: AsyncIOMotorDatabase = Depends(get_mongo_db)
