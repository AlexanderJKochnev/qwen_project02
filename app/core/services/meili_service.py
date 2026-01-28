# app.core.services.meili_service.py
""" обработка очереди на индексацию Meilisearch """
import asyncio
from meilisearch_python_sdk import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from app.core.models.outbox_model import MeiliOutbox, OutboxStatus, OutboxAction
from app.core.config.database.db_async import DatabaseManager, get_db
from app.core.config.database.meili_async import MeiliManager, get_meili_client


class MeiliOutboxProcessor:
    @staticmethod
    async def process_queue(db_session: AsyncSession, meili_client: AsyncClient):
        # За один раз берем задачи для ВСЕХ индексов
        stmt = (select(MeiliOutbox).where(MeiliOutbox.status == OutboxStatus.PENDING).order_by(
            MeiliOutbox.created_at
        ).limit(
            100
        ).with_for_update(skip_locked=True))
        result = await db_session.execute(stmt)
        tasks = result.scalars().all()

        if not tasks:
            return False

        for task in tasks:
            try:
                # Нам не нужен специфичный сервис, Meilisearch Client работает через UID индекса
                index = meili_client.index(task.index_name)

                if task.action in [OutboxAction.CREATE, OutboxAction.UPDATE]:
                    # В task.payload уже лежит готовый вложенный JSON от Pydantic
                    await index.add_documents([task.payload])

                elif task.action == OutboxAction.DELETE:
                    await index.delete_document(task.record_id)

                await db_session.delete(task)
            except Exception as e:
                logger.error(f"Failed task {task.id} for index {task.index_name}: {e}")
                task.status = OutboxStatus.FAILED
                task.retry_count += 1

        await db_session.commit()
        logger.success("MeiliOutbox: Успешно синхронизировано операций с Meilisearch")
        return True


class MeiliSyncManager:
    _lock = asyncio.Lock()

    @classmethod
    async def run_sync(cls, session: AsyncSession):
        """
        Точка входа для синхронизации.
        Безопасно запускается из любого места.
        """
        logger.error("MeiliSync: start.")
        if cls._lock.locked():
            logger.debug("MeiliSync: Синхронизация уже запущена другим процессом, пропускаю.")
            return

        async with cls._lock:
            logger.info("MeiliSync: Начало обработки очереди...")
            try:
                processed_any = True
                while processed_any:
                    # session = get_db()
                    # client = get_meili_client()
                    processed_any = await MeiliOutboxProcessor.process_queue(session)
                    # async with DatabaseManager.session_maker() as session:
                    client = await MeiliManager.get_client()
                    # Метод должен возвращать True, если задачи были найдены и обработаны
                    processed_any = await MeiliOutboxProcessor.process_queue(session, client)
                logger.info("MeiliSync: Очередь пуста, синхронизация завершена.")
            except Exception as e:
                logger.error(f"MeiliSync: Критическая ошибка при синхронизации: {e}")
