# app.core.services.meili_service.py
""" обработка очереди на индексацию Meilisearch """
from meilisearch_python_sdk import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger
from app.core.models.outbox_model import MeiliOutbox, OutboxStatus, OutboxAction


class MeiliOutboxProcessor:
    @staticmethod
    async def process_queue(db_session: AsyncSession, meili_client: AsyncClient):
        # 1. Берем пачку задач (например, 50 за раз)
        # SKIP LOCKED позволяет запускать несколько воркеров параллельно без конфликтов
        stmt = (select(MeiliOutbox).where(MeiliOutbox.status == OutboxStatus.PENDING).limit(50).with_for_update(
            skip_locked=True
        ))
        result = await db_session.execute(stmt)
        tasks = result.scalars().all()

        if not tasks:
            return

        # 2. Обрабатываем задачи
        # Для оптимизации можно было бы группировать по index_name,
        # но для начала реализуем надежный последовательный цикл.
        for task in tasks:
            index = meili_client.index(task.index_name)
            try:
                if task.action in [OutboxAction.CREATE, OutboxAction.UPDATE]:
                    # В Meilisearch add_documents делает и вставку, и обновление
                    await index.add_documents([task.payload])

                elif task.action == OutboxAction.DELETE:
                    await index.delete_document(task.record_id)

                # Если успешно — удаляем из очереди
                await db_session.delete(task)

            except Exception as e:
                logger.error(f"Ошибка Meilisearch (Task ID: {task.id}): {e}")
                task.status = OutboxStatus.FAILED
                task.retry_count += 1
                if task.retry_count > 5:
                    # Можно переместить в архив или пометить как безнадежный
                    task.status = OutboxStatus.FAILED

                    # 3. Фиксируем очистку очереди в БД
        await db_session.commit()
