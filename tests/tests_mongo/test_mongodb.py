# tests/test_mongodb.py
# тесты запускать по одному иначе падают - особенность mongodb

import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from tests.config import settings_db

pytestmark = pytest.mark.asyncio


async def test_direct_mongo_connection():
    """Прямое тестирование подключения к MongoDB"""
    try:
        # mongo_url = settings_db.mongo_url
        mongo_url = 'mongodb://admin:admin@localhost:27017'
        client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=500)
        # Проверяем подключение
        await client.admin.command('ping')
        client.close()
        assert True, "MongoDB connection unsuccessful"
    except Exception as e:
        print(f"Direct connection failed: {e}")
        assert False, f"{e} {mongo_url=}"


@pytest.mark.skip
async def test_mongo_health_check(test_mongodb):
    """Тестирует health check MongoDB подключения - ДОЛЖЕН ПАДАТЬ при проблемах"""
    # Проверяем что можем выполнять команды
    try:
        result = await test_mongodb.client.admin.command('ping')
        assert result["ok"] == 1.0, "MongoDB ping command failed"
    except Exception as e:
        pytest.fail(f"MongoDB health check failed: {e}")
