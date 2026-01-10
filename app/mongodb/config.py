# app/mongodb/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from fastapi import Depends  # NOQA: F401
from typing import Optional
from app.core.config.project_config import get_path_to_root, settings
# import os


class MongoDB:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None

    async def connect(self, connection_string: str, database_name: str):
        if self.client is None:
            self.client = AsyncIOMotorClient(connection_string)
            self.database = self.client[database_name]

    async def disconnect(self):
        if self.client:
            self.client.close()
            self.client = None
            self.database = None


mongodb = MongoDB()


# зависимость client+database для использования в роутах
async def get_mongodb():
    return mongodb


# зависимость только database для использования в роутах
async def get_database(mongodb_instance: MongoDB = Depends(get_mongodb)):
    if mongodb_instance.database is None:
        default_url = settings.mongo_url
        default_db = settings.MONGO_DATABASE
        await mongodb_instance.connect(default_url, default_db)
    return mongodb_instance.database
