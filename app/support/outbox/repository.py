# app/support/outbox/repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Any
from loguru import logger
from pydantic import BaseModel
from app.support.outbox.model import OutboxAction, OutboxStatus, MeiliOutbox


class BaseRepository:
    def __init__(self, model: Any, meili_service):  # BaseMeiliService):
        self.model = model
        self.meili = meili_service

    @classmethod
    async def _add_to_outbox(cls, session: AsyncSession, action: OutboxAction, record_id: Any, payload: dict = None):
        try:
            outbox_entry = MeiliOutbox(
                index_name=cls.meili.index_name,
                action=action,
                record_id=str(record_id),
                payload=payload,
                status=OutboxStatus.PENDING
            )
            session.add(outbox_entry)
        except SQLAlchemyError as e:
            # Если таблицы нет или произошла ошибка БД
            session.expunge(outbox_entry)  # Убираем проблемный объект из сессии
            logger.error(
                f"Критическая ошибка Outbox: {e}. Данные не будут синхронизированы с Meilisearch!"
            )
            # Здесь мы НЕ пробрасываем ошибку дальше (raise),
            # чтобы основной метод (create/update) смог завершить commit в основную таблицу.

    async def create(self, session: AsyncSession, schema: BaseModel):
        # 1. Создаем объект
        db_obj = self.model(**schema.model_dump())
        session.add(db_obj)
        await session.flush()  # Получаем ID без коммита

        # 2. Формируем payload через Pydantic схему сервиса
        payload = self.meili.schema.model_validate(db_obj).model_dump(mode='json')

        # 3. Пишем в Outbox (в этой же транзакции)
        await self._add_to_outbox(session, OutboxAction.CREATE, db_obj.id, payload)

        await session.commit()
        await session.refresh(db_obj)
        return db_obj

    async def update(self, session: AsyncSession, db_obj: Any, update_data: dict):
        for key, value in update_data.items():
            setattr(db_obj, key, value)

        await session.flush()
        # Для Meilisearch UPDATE — это частичный payload с ID
        payload = {"id": db_obj.id, **update_data}

        await self._add_to_outbox(session, OutboxAction.UPDATE, db_obj.id, payload)
        await session.commit()
        return db_obj

    async def delete(self, session: AsyncSession, db_obj: Any):
        obj_id = db_obj.id
        await session.delete(db_obj)
        await self._add_to_outbox(session, OutboxAction.DELETE, obj_id)
        await session.commit()
