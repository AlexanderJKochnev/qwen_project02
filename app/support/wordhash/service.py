# app.support.wordhash.service.py
import asyncio

from loguru import logger

# services/wordhash_service.py
from app.core.hash_norm import get_cached_hash
from app.core.services.service import Service
from app.core.utils.backgound_tasks import background_unique
from app.support.wordhash.repository import WordHashRepository


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
