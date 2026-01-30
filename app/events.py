# app.events.py
import asyncio
import psycopg
from loguru import logger
from sqlalchemy import event, update, text
from app.core.models.base_model import Base
from app.core.utils.common_utils import get_owners_by_path
from app.service_registry import _SEARCH_DEPENDENCIES
from app.core.config.database.db_config import settings_db
from app.core.services.service import Service


@event.listens_for(Base, "after_update", propagate=True)
def trigger_reindex(mapper, connection, target):
    logger.debug(f"SQLAlchemy поймал UPDATE модели: {target.__class__.__name__}")
    model_cls = target.__class__

    if model_cls in _SEARCH_DEPENDENCIES:
        path = _SEARCH_DEPENDENCIES[model_cls]
        owners = get_owners_by_path(target, path)

        if not owners:
            return

        # Группируем ID по классам моделей (на случай, если путь ведет к разным типам)
        updates = {}
        for owner in owners:
            owner_cls = owner.__class__
            # Проверяем, есть ли у модели наше поле (через Mixin или inspect)
            if hasattr(owner_cls, 'search_content'):
                updates.setdefault(owner_cls, set()).add(owner.id)

        # Выполняем UPDATE для каждого типа модели
        for cls, ids in updates.items():
            print(f"[DEBUG] Сброс индекса для {cls.__name__}, IDs: {ids}")
            connection.execute(
                update(cls).where(cls.id.in_(ids)).values(search_content=None)
            )

            connection.execute(text("NOTIFY search_reindex;"))


async def pg_listen_worker():
    """
    Фоновый воркер на psycopg 3 для прослушивания канала search_reindex.
    """
    # Формируем строку подключения (psycopg3 использует стандартный формат)
    print("\n\nHELLO FROM WORKER\n\n", flush=True)
    try:
        conn_str = str(settings_db.database_url).replace("postgresql+psycopg://", "postgresql://")
        print(conn_str)
    except Exception as e:
        print("\n\n", e)
    while True:
        try:
            # Открываем асинхронное соединение
            async with await psycopg.AsyncConnection.connect(conn_str, autocommit=True) as conn:
                async with conn.cursor() as cur:
                    await cur.execute("LISTEN search_reindex;")
                    print("[INFO] Psycopg слушатель запущен (канал: search_reindex)...")

                    # Итерируемся по уведомлениям (этот цикл ждет сигналов без нагрузки на CPU)
                    async for notify in conn.notifies():
                        print(f"[NOTIFY] Сигнал получен: {notify.channel}. Запуск переиндексации...")
                        # Запускаем задачу переиндексации
                        asyncio.create_task(Service.reindex_all_searchable_models(500))

        except Exception as e:
            print(f"[ERROR] Ошибка слушателя: {e}. Переподключение через 5 сек...")
            await asyncio.sleep(5)
