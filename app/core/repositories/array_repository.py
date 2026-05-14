# app.core.repository.array_repository.py
"""
    методы SQLAlchemy repository для работы с полями  ARRAY[]
"""
from typing import List
from sqlalchemy import func, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.utils.common_utils import getter, setter
from app.core.types import ModelType


class ArrayRepository:

    @classmethod
    async def get_array(cls, id: int, model: ModelType,
                        arrayName: str, session: AsyncSession) -> List[str]:
        """ получение instance только с полем массива """
        field = getter(model, arrayName)
        result = await session.execute(select(field).where(model.id == id))
        if not result:
            return None
        return list(result.scalar_one_or_none())

    @classmethod
    async def set_array(cls, id: int, model: ModelType,
                        arrayName: str, values: List[str], session: AsyncSession):
        """ сохранение значения в поле массива """
        stmt = update(model).where(model.id == id).values(**{arrayName: values})
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def get_array_by_id(cls, id: int, model: ModelType,
                              arrayName: str, session: AsyncSession) -> List[str]:
        """ получение массива по id """
        return await cls.get_array(id, model, arrayName, session)

    @classmethod
    async def add_to_array(cls, id: int, new_elements: list[str],
                           model: ModelType, arrayName: str,
                           session: AsyncSession) -> None:
        """
            Добавление элементов в конец массива
            id:             id записи
            new_elements:   добавляемые элементы
            model:          модель
            arrayName:      имя поля
        """
        array_list: List[str] = await cls.get_array(id, model, arrayName, session)
        array_list.extend(new_elements)
        await cls.set_array(id, model, arrayName, array_list, session)
        return {'update_array': array_list}
        # stmt = update(model).where(model.id == id).values(**{field.name: func.array_cat(field, new_elements)})
        # await session(stmt)
