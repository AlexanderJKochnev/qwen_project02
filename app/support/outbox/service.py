# app/support/outbox/service.py

from sqlalchemy import select
from meilisearch_python_sdk import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.support.outbox.model import MeiliOutbox, OutboxAction, OutboxStatus

import functools
import logging
from typing import Type, Any
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def sync_with_meilisearch(schema: Type[BaseModel], action: OutboxAction, index_name: str):
    """
    Декоратор для методов Service Layer.
    schema: Pydantic модель для индексации.
    action: Тип операции (CREATE, UPDATE, DELETE).
    использование
    @sync_with_meilisearch(schema=ItemReadRelationSchema, action=OutboxAction.CREATE, index_name: 'item')
    @classmethod
    async def create(cls, data, repository: Type[Repository], model: ModelType,
                     session: AsyncSession) -> dict:
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 1. Выполняем основной метод сервиса (создание/обновление в БД)
            result = await func(*args, **kwargs)

            # 2. Ищем сессию в аргументах метода (она нужна для записи в Outbox)
            session: AsyncSession = kwargs.get("session") or next(
                (a for a in args if isinstance(a, AsyncSession)), None
            )

            if not session:
                logger.error(f"Session not found in {func.__name__}. Outbox sync skipped.")
                return result

            try:
                # 3. Валидируем результат через Pydantic-схему (собираем вложенный словарь)
                # Если result — это dict или модель SQLAlchemy, Pydantic это обработает
                meili_data = schema.model_validate(result).model_dump(mode='json')

                # 4. Пишем в Outbox в той же транзакции
                # index_name = result.__class__.__name__.lower() if not isinstance(
                #     result, dict
                # ) else schema.__name__.lower()

                outbox_entry = MeiliOutbox(
                    index_name=index_name, action=action, record_id=str(meili_data.get("id")),
                    payload=meili_data, status=OutboxStatus.PENDING
                )
                session.add(outbox_entry)  # Мы не делаем commit здесь! Роутер или сервис сделают его позже.

            except Exception as e:
                # Ошибка валидации или Outbox не должна прерывать работу основного сервиса
                logger.error(f"Failed to queue Meilisearch sync: {e}")

            return result

        return wrapper

    return decorator


class MeiliOutboxProcessor:
    @staticmethod
    async def process_pending_tasks(session: AsyncSession, meili_client: AsyncClient):
        # 1. Получаем пачку задач (SELECT FOR UPDATE SKIP LOCKED для параллелизма)
        stmt = (select(MeiliOutbox).where(MeiliOutbox.status == OutboxStatus.PENDING).limit(50).with_for_update(
            skip_locked=True
        ))
        result = await session.execute(stmt)
        tasks = result.scalars().all()

        for task in tasks:
            index = meili_client.index(task.index_name)
            try:
                if task.action == OutboxAction.CREATE or task.action == OutboxAction.UPDATE:
                    # add_documents в Meili работает и как создание, и как обновление
                    await index.add_documents([task.payload])

                elif task.action == OutboxAction.DELETE:
                    await index.delete_document(task.record_id)

                # В 2026 году можно не ждать task_uid, если Meilisearch доступен.
                # Удаляем запись из Outbox после успешной отправки в Meili
                await session.delete(task)

            except Exception as e:
                print(f"Meilisearch sync failed for task {task.id}: {e}")
                task.status = OutboxStatus.FAILED
                task.retry_count += 1

        await session.commit()
