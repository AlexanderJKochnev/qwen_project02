# app.core.service.array_service.py
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.types import ModelType
from app.core.repositories.array_repository import ArrayRepository


class ArrayService:
    """
        service  ice layer для работы с полями  ARRAY[]
    """

    @classmethod
    async def get_array_by_id(cls, id: int,
                              model: ModelType, arrayName: str,
                              repository: ArrayRepository,
                              session: AsyncSession) -> Dict[str, Any]:
        """ получение массива по id """
        result = await repository.get_array_by_id(id, model, arrayName, session)
        return {'arrray': result, 'size': len(result) if result else 0}

    @classmethod
    async def add_to_array(cls, id: int, new_elements: List[str],
                           model: ModelType, arrayName: str,
                           repository: ArrayRepository,
                           session: AsyncSession) -> None:
        """
            Добавление элементов в конец массива
            id:             id записи
            new_elements:   добавляемые элементы
            model:          модель
            arrayName:      имя поля
        """
        return await repository.add_to_array(id, new_elements, model, arrayName, session)

        array_list: List[str] = await cls.get_array(id, model, arrayName, session)
        array_list.extend(new_elements)
        await cls.set_array(id, model, arrayName, array_list, session)
        return {'update_array': array_list}
        # stmt = update(model).where(model.id == id).values(**{field.name: func.array_cat(field, new_elements)})
        # await session(stmt)
