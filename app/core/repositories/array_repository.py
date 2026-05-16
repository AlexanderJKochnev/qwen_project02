# app.core.repository.array_repository.py
"""
    методы SQLAlchemy repository для работы с полями  ARRAY[]
"""
from typing import List
from sqlalchemy import update, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.utils.common_utils import getter
from app.core.types import ModelType
from loguru import logger


class ArrayRepository:
    """
    dict_list = result.mappings().all()  список словарей
    one_row_dict = result.mappings().first()  один словарь
    one_row_dict = result.mappings().one_or_none()  один словарь или ничего !
    1. get_array
    2. add array to the end
    3. replace all array
    4. delete all array
    5. add array first
    """

    @classmethod
    async def _get_array_(cls, id: int, model: ModelType,
                          arrayName: str, session: AsyncSession) -> list:
        """ получение instance только с полем массива """
        field = getter(model, arrayName)
        result = await session.execute(select(field).where(model.id == id))
        if not result:
            return []
        res = result.mappings().one_or_none()
        return res.get(arrayName) or []

    @classmethod
    async def _set_array_(cls, id: int, model: ModelType,
                          arrayName: str, values: List[str], session: AsyncSession):
        """ сохранение значения в поле массива """
        stmt = update(model).where(model.id == id).values(**{arrayName: values})
        await session.execute(stmt)
        await session.commit()

    @classmethod
    async def get_array_by_id(cls, id: int, model: ModelType,
                              arrayName: str, session: AsyncSession) -> List[str]:
        """ получение массива по id """
        return await cls._get_array_(id, model, arrayName, session)

    @classmethod
    async def add_to_array(cls, id: int, new_elements: list[str],
                           model: ModelType, arrayName: str,
                           session: AsyncSession) -> list:
        """
            Добавление элементов в конец массива
            id:             id записи
            new_elements:   добавляемые элементы
            model:          модель
            arrayName:      имя поля
        """
        array_list: List[str] = await cls._get_array_(id, model, arrayName, session)
        array_list.extend(new_elements)
        await cls._set_array_(id, model, arrayName, array_list, session)
        return array_list

    @classmethod
    async def add_first_to_array(cls, id: int, new_elements: list[str],
                                 model: ModelType, arrayName: str,
                                 session: AsyncSession) -> list:
        """
            Добавление элементов в начало массива
            id:             id записи
            new_elements:   добавляемые элементы
            model:          модель
            arrayName:      имя поля
        """
        array_list: List[str] = await cls._get_array_(id, model, arrayName, session)
        new_elements.extend(array_list)
        await cls._set_array_(id, model, arrayName, new_elements, session)
        return new_elements

    @classmethod
    async def clear_array_by_id(
        cls, id: int, model: ModelType, arrayName: str, session: AsyncSession
    ) -> List[str]:
        """ очистка массива по id """
        await cls._set_array_(id, model, arrayName, [], session)
        return await cls._get_array_(id, model, arrayName, session)

    @classmethod
    async def replace_array(cls, id: int, new_elements: list[str],
                            model: ModelType, arrayName: str,
                            session: AsyncSession) -> list:
        """
            замена всех элементов в массиве
            id:             id записи
            new_elements:   добавляемые элементы
            model:          модель
            arrayName:      имя поля
        """
        await cls._set_array_(id, model, arrayName, new_elements, session)
        return new_elements

    @classmethod
    async def del_by_index_array(
        cls, id: int, pos: int, model: ModelType, arrayName: str, session: AsyncSession
    ) -> list:
        """
            удаление элемента по индексу
            id:             id записи
            new_elements:   добавляемые элементы
            model:          модель
            arrayName:      имя поля
        """
        array_list: List[str] = await cls._get_array_(id, model, arrayName, session)
        if len(array_list) > 0 and pos <= len(array_list):
            array_list.pop(pos)
            await cls._set_array_(id, model, arrayName, array_list, session)
        return array_list

    @classmethod
    async def split_by_index_array(
        cls, id: int, pos1: int, pos2: int, model: ModelType, arrayName: str, session: AsyncSession
    ) -> list:
        """
            поменять два элемента местами
            id:             id записи
            new_elements:   добавляемые элементы
            model:          модель
            arrayName:      имя поля
        """
        array_list: List[str] = await cls._get_array_(id, model, arrayName, session)
        if len(array_list) > 0 and pos1 <= len(array_list) and pos2 <= len(array_list):
            array_list[pos1], array_list[pos2] = array_list[pos2], array_list[pos1]
            await cls._set_array_(id, model, arrayName, array_list, session)
        return array_list

    @classmethod
    async def replace_by_index_array(
        cls, id: int, pos: int, newdata: str, model: ModelType, arrayName: str, session: AsyncSession
    ) -> list:
        """
            заменить
            id:             id записи
            new_elements:   добавляемые элементы
            model:          модель
            arrayName:      имя поля
        """
        array_list: List[str] = await cls._get_array_(id, model, arrayName, session)
        if len(array_list) > 0 and pos <= len(array_list):
            array_list[pos] = newdata
            await cls._set_array_(id, model, arrayName, array_list, session)
        return array_list
