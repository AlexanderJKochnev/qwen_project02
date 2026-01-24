# app/utils/search_sync.py
""" поисковый сервис meilisearch вместо встроенных индексов """

import asyncio
from typing import List, Type, Any, Optional, Set
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy import and_, or_
from pydantic import BaseModel
from loguru import logger
import meilisearch
from meilisearch.errors import MeiliSearchApiError
from app.core.config.project_config import settings


# Настройки — лучше вынести в settings.py или .env
MEILISEARCH_URL = settings.MEILISEARCH_URL
MEILISEARCH_MASTER_KEY = settings.MEILISEARCH_MASTER_KEY


class SearchSyncError(Exception):
    """Исключение для ошибок синхронизации поиска."""
    pass


def get_meilisearch_client() -> meilisearch.Client:
    return meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_MASTER_KEY)


def _ensure_utc(dt: datetime) -> datetime:
    """Приводит datetime к UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


async def incremental_sync_model_to_meilisearch(
    db: AsyncSession,
    model_class: Type[Any],
    search_schema: Type[BaseModel],
    index_name: str,
    last_sync_time: datetime,
    id_field: str = "id",
    updated_at_field: str = "updated_at",
    query_options: Optional[List] = None,
    batch_size: int = 500,
) -> datetime:
    """
    Выполняет инкрементальную синхронизацию: обновляет и удаляет документы.

    :param last_sync_time: время последней успешной синхронизации (UTC)
    :return: новое время последней синхронизации (на основе max(updated_at))
    """
    logger.info(f"Инкрементальная синхронизация {model_class.__name__} с {last_sync_time}")

    try:
        # === 1. Получаем все записи, изменённые после last_sync_time ===
        updated_col = getattr(model_class, updated_at_field)
        query = db.query(model_class).filter(updated_col > last_sync_time)
        if query_options:
            for opt in query_options:
                query = query.options(opt)
        changed_records = await query.all()

        # === 2. Собираем ID для удаления (где deleted_at IS NOT NULL или is_deleted=True) ===
        # Поддержка soft-delete через поле `deleted_at` (datetime) или `is_deleted` (bool)
        deleted_ids: Set[int] = set()

        for record in changed_records[:]:  # копия для безопасного удаления из списка
            # Вариант A: soft-delete через deleted_at
            if hasattr(record, 'deleted_at') and record.deleted_at is not None:
                deleted_ids.add(getattr(record, id_field))
                changed_records.remove(record)
                continue
            # Вариант B: soft-delete через is_deleted
            if hasattr(record, 'is_deleted') and record.is_deleted:
                deleted_ids.add(getattr(record, id_field))
                changed_records.remove(record)
                continue

        # === 3. Преобразуем оставшиеся в документы ===
        documents = []
        for record in changed_records:
            try:
                doc = search_schema.from_orm_with_relations(record).model_dump()
                if id_field not in doc:
                    raise ValueError(f"Отсутствует '{id_field}' в документе")
                documents.append(doc)
            except Exception as e:
                logger.error(f"Ошибка преобразования записи {record}: {e}")
                raise SearchSyncError("Ошибка сериализации документа") from e

        # === 4. Отправляем в Meilisearch ===
        client = get_meilisearch_client()
        index = client.index(index_name)

        # Удаляем помеченные как удалённые
        if deleted_ids:
            logger.info(f"Удаление {len(deleted_ids)} документов из Meilisearch")
            task = index.delete_documents(list(deleted_ids))
            client.wait_for_task(task.task_uid, timeout_in_ms=30000)

        # Обновляем/добавляем изменённые
        if documents:
            logger.info(f"Обновление {len(documents)} документов в Meilisearch")
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                task = index.add_documents(batch)
                client.wait_for_task(task.task_uid, timeout_in_ms=60000)
        else:
            logger.debug("Нет изменённых документов для обновления")

        # === 5. Определяем новое время синхронизации ===
        if changed_records:
            max_updated = max(
                _ensure_utc(getattr(r, updated_at_field)) for r in changed_records
            )
        else:
            max_updated = last_sync_time

        logger.info(f"✅ Инкрементальная синхронизация завершена. Новое время: {max_updated}")
        return max_updated

    except Exception as e:
        logger.error(f"Ошибка инкрементальной синхронизации: {e}")
        raise SearchSyncError("Инкрементальная синхронизация не удалась") from e