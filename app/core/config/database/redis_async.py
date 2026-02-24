# app.core.config.databse.redis_async.py
# app/core/redis_config.py
from redis.asyncio import ConnectionPool, Redis
from loguru import logger


class RedisManager:
    def __init__(self):
        self.pool: ConnectionPool = None

    async def connect(self, host: str, port: int):
        """Асинхронная инициализация пула и проверка связи"""
        self.pool = ConnectionPool(
            host=host,
            port=port,
            db=0,
            decode_responses=False,  # False для работы со сжатыми (bytes) данными
            max_connections=2
        )
        # Проверка: создаем временный клиент и пингуем базу
        client = Redis(connection_pool=self.pool)
        try:
            await client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            raise e

    async def disconnect(self):
        """Асинхронное закрытие всех соединений"""
        if self.pool:
            await self.pool.disconnect()
            logger.info("🛑 Redis pool disconnected")

    def get_client(self) -> Redis:
        """Возвращает готовый клиент, привязанный к пулу"""
        return Redis(connection_pool=self.pool)


# Создаем глобальный экземпляр менеджера
redis_manager = RedisManager()
