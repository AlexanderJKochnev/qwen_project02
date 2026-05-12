# app.support.merging.repository.py
from loguru import logger
from sqlalchemy import Select, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.support.item.model import Item
from app.support.drink.repository import DrinkRepository


class MergingRepository(DrinkRepository):

    @classmethod
    def get_distill_query(cls) -> Select:
        return select(cls.model)

    @classmethod
    def get_drinks_by_ids(cls, ids: list, session: AsyncSession):
        stmt = cls.get_distill_query().where(cls.model.id.in_(ids)).order_by(cls.model.id.asc())
        return cls.nonpagination(stmt, session)

    from sqlalchemy import select

    @classmethod
    async def get_and_merge_pairs_batched(
            cls, pairs_ids: list[tuple[int, int]], session: AsyncSession, chunk_size: int = 500
    ):
        """
        Объединение похожих записей с полседующим удалением одной из них
        Обработка большого количества пар через разделение на части.
        """
        total_processed = 0

        # Разбиваем весь список пар на чанки (например, по 500 пар за раз)
        for i in range(0, len(pairs_ids), chunk_size):
            chunk = pairs_ids[i: i + chunk_size]

            # Собираем ID только для текущего чанка
            current_ids = set()
            for t_id, s_id in chunk:
                current_ids.update([t_id, s_id])

            # Загружаем объекты текущего чанка
            stmt = cls.get_distill_query().where(cls.model.id.in_(current_ids))
            result = await session.execute(stmt)
            objects_map = {obj.id: obj for obj in result.scalars().all()}

            # Формируем пары инстансов
            ready_pairs = []
            for t_id, s_id in chunk:
                target = objects_map.get(t_id)
                source = objects_map.get(s_id)
                if target and source:
                    ready_pairs.append((target, source))

            # Выполняем слияние для текущего чанка
            if ready_pairs:
                await cls._execute_merge_logic(ready_pairs, session)
                total_processed += len(ready_pairs)

                # Фиксируем изменения в БД для текущего чанка и очищаем память
                await session.flush()  # session.expunge_all() -- раскомментируй, если объектов ОЧЕНЬ много и память течет
        all_source_ids = set(id for _, id in pairs_ids)
        logger.warning(all_source_ids)
        if all_source_ids:
            # Используем delete() вместо session.delete() для скорости и избежания проблем с объектами в памяти
            model = Item
            # await session.execute(delete(model).where(model.drink_id.in_(all_source_ids)))
            # await session.execute(delete(cls.model).where(cls.model.id.in_(all_source_ids)))
            await session.flush()

        return {"success": True, "total_processed": total_processed, "deleted_records": len(all_source_ids)}

    @staticmethod
    async def _execute_merge_logic(pairs: list[tuple], session: AsyncSession):
        for target, source in pairs:
            # Сравниваем только через __table__.columns, чтобы не дергать лишние методы
            for column in target.__table__.columns.keys():
                if column == 'id':
                    continue
                t_val = getattr(target, column)
                s_val = getattr(source, column)

                if t_val in (None, 0, '') and s_val not in (None, 0, ''):
                    setattr(target, column, s_val)
                    logger.warning(f'{column}: {t_val}, {s_val}')