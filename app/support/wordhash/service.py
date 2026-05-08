# app.support.wordhash.service.py
import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
# services/wordhash_service.py
from app.core.hash_norm import get_cached_hash
from app.core.services.service import Service
from app.core.utils.backgound_tasks import background_unique
from app.support.wordhash.repository import WordHashRepository
from app.dependencies import ClickHouseRepositoryFactory, get_clickhouse_repository_factory
from app.core.config.database.db_async import get_db


class WordHashService(Service):

    @classmethod
    async def rebuild_all_hashes(cls, background_tasks, session_factory):
        """Точка входа - запуск пересчета"""
        return await cls._run_rebuild_stream(session_factory=session_factory, background_tasks=background_tasks)

    @classmethod
    @background_unique
    async def _run_rebuild_stream(cls, session_factory):
        """Фоновая задача пересчета через stream"""
        async with session_factory() as session:
            try:
                logger.info("🚀 Запуск полного пересчета WordHash")
                start_time = asyncio.get_event_loop().time()

                chunk_size = 1000
                chunk = []
                updated_count = 0

                async for word in WordHashRepository.get_all_words_stream(session):
                    chunk.append(word)

                    if len(chunk) >= chunk_size:
                        # Пересчитываем хэши
                        updates = [{'word': w, 'hash': get_cached_hash(w)} for w in chunk]

                        # Обновляем в БД
                        await WordHashRepository.bulk_update_hashes(session, updates)
                        updated_count += len(chunk)

                        logger.debug(f"📦 Обработано {updated_count} слов")
                        chunk = []

                        # Даем время другим задачам
                        await asyncio.sleep(0.01)

                # Обрабатываем остаток
                if chunk:
                    updates = [{'word': w, 'hash': get_cached_hash(w)} for w in chunk]
                    await WordHashRepository.bulk_update_hashes(session, updates)
                    updated_count += len(chunk)

                await session.commit()

                elapsed = asyncio.get_event_loop().time() - start_time
                logger.success(
                    f"✅ Пересчет завершен: {updated_count} слов за {elapsed:.1f} сек, скорость: {updated_count / elapsed:.0f} слов/сек"
                )

            except Exception as e:
                await session.rollback()
                logger.error(f"❌ Ошибка пересчета: {e}")
                raise


class ClickHashService:
    def __init__(self, session: AsyncSession = Depends(get_db),
                 click_repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory),
                 ):
        self.click_repo = click_repo_factory.for_table('beverages_words')
        # logger.warning(f"DEBUG: repo.client type = {type(self.click_repo.client)}")  # Должно быть AsyncClient
        self.repository = WordHashRepository

    async def get(self, limit: int = 30, page: int = 1) -> dict:
        """
            получение данных из clickhouse
        """
        order_by: str = 'word'
        fields: list = ['word', 'hash', 'freq']
        response = await self.click_repo.get(order_by, limit, page, fields)
        return {'result': response}