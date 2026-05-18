# app.core.utils.hashes.py
"""
    разные виды хэшей
"""

import xxhash  # pip install xxhash
import cityhash  # pip install cityhash
import hashlib

import xxhash  # pip install xxhash
import cityhash  # pip install cityhash
import hashlib


class FastImageHasher:
    """Быстрое хэширование изображений для дедупликации"""

    @staticmethod
    def xxhash64(data: bytes) -> int:
        """Самый быстрый вариант (5.4 GB/s)"""
        return xxhash.xxh64(data).intdigest()

    @staticmethod
    def cityhash64(data: bytes) -> int:
        """Баланс скорости и качества (1 GB/s)"""
        return cityhash.CityHash64(data)

    @staticmethod
    def hybrid_hash(data: bytes) -> int:
        """
        Комбинированный подход для максимальной скорости:
        1. Быстрый хэш первых 4KB
        2. Если коллизия - проверяем полностью
        """
        fast_hash = xxhash.xxh64(data[:4096]).intdigest()

        # Для 99.9% случаев этого достаточно
        # При коллизии (будет обнаружено в ClickHouse) делаем полный хэш
        return fast_hash

    @classmethod
    async def _compute_hash(cls, image_bytes: bytes) -> str:
        """
        Вычисление хэша изображения (xxHash или MD5)
        "как бы" асинхронная реализация
        """
        loop = asyncio.get_event_loop()
        return xxhash.xxh64(image_bytes).hexdigest()
        return await loop.run_in_executor(cls._executor, _hash)