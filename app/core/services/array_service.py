# app.core.service.array_service.py
from typing import Any, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.types import ModelType
from app.core.repositories.array_repository import ArrayRepository
from app.core.services.seaweed_service import SeaweedsService
from app.core.utils.alchemy_utils import has_column


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
    async def get_item_of_array_by_id(
            cls, id: int,
            model: ModelType, arrayName: str,
            repository: ArrayRepository, session: AsyncSession,
            pos: int = 0
            ) -> Any:
        """ получение элемента массива по id и индексу"""
        result = await repository.get_array_by_id(id, model, arrayName, session)
        if result:
            return result[min(len(result), pos)]
        else:
            return None

    @classmethod
    async def add_to_array(cls, id: int, new_elements: List[str],
                           model: ModelType, arrayName: str,
                           repository: ArrayRepository,
                           session: AsyncSession) -> Dict:
        """
            Добавление элементов в конец массива
            id:             id записи
            new_elements:   добавляемые элементы
            model:          модель
            arrayName:      имя поля
        """
        result = await repository.add_to_array(id, new_elements, model, arrayName, session)
        return {'arrray': result, 'size': len(result) if result else 0}

    @classmethod
    async def clear_array_by_id(cls, id: int,
                                model: ModelType, arrayName: str,
                                repository: ArrayRepository,
                                session: AsyncSession) -> Dict[str, Any]:
        """ получение массива по id """
        result = await repository.clear_array_by_id(id, model, arrayName, session)
        return {'arrray': result, 'size': len(result) if result else 0}

    @classmethod
    async def add_first_to_array(cls, id: int, new_elements: List[str],
                                 model: ModelType, arrayName: str,
                                 repository: ArrayRepository,
                                 session: AsyncSession) -> Dict[str, Any]:
        """ Добавление элементов в начало массива """
        result = await repository.add_first_to_array(id, new_elements, model, arrayName, session)
        return {'arrray': result, 'size': len(result) if result else 0}

    @classmethod
    async def replace_array(cls, id: int, new_elements: List[str],
                            model: ModelType, arrayName: str,
                            repository: ArrayRepository,
                            session: AsyncSession) -> Dict[str, Any]:
        """ Замена всех элементов в массиве """
        result = await repository.replace_array(id, new_elements, model, arrayName, session)
        return {'arrray': result, 'size': len(result) if result else 0}

    @classmethod
    async def del_by_index_array(cls, id: int, pos: int,
                                 model: ModelType, arrayName: str,
                                 repository: ArrayRepository,
                                 session: AsyncSession) -> Dict[str, Any]:
        """ Удаление элемента по индексу """
        result = await repository.del_by_index_array(id, pos, model, arrayName, session)
        return {'arrray': result, 'size': len(result) if result else 0}

    @classmethod
    async def split_by_index_array(cls, id: int, pos1: int, pos2: int,
                                   model: ModelType, arrayName: str,
                                   repository: ArrayRepository,
                                   session: AsyncSession) -> Dict[str, Any]:
        """ Поменять два элемента местами """
        result = await repository.split_by_index_array(id, pos1, pos2, model, arrayName, session)
        return {'arrray': result, 'size': len(result) if result else 0}

    @classmethod
    async def replace_by_index_array(cls, id: int, pos: int, newdata: str,
                                     model: ModelType, arrayName: str,
                                     repository: ArrayRepository,
                                     session: AsyncSession) -> Dict[str, Any]:
        """ Замена элемента по индексу на новые данные """
        result = await repository.replace_by_index_array(id, pos, newdata, model, arrayName, session)
        return {'arrray': result, 'size': len(result) if result else 0}

    # -----
    @classmethod
    async def get_image_by_id_v2(
            cls, id: int, repository: Repository, model: ModelType, session: AsyncSession,
            image_service: SeaweedsService
    ):
        """
            получение полноразмерного изображения по id напитка
        """
        #  ПОИСК КОЛОНКИ seaweed_fids
        arrayColname = 'seaweed_fids'
        if not has_column(model, arrayColname):
            raise HTTPException(status_code=422, detail=f'{model.__name__} model has no images at all')
        # 1. получение image_id by id
        image_id = await cls.get_item_of_array_by_id(id, model, arrayColname, repository, session, 0)
        if not image_id:
            # СЮДА ПОСТАВИТЬ ЗАГЛУШКУ
            raise HTTPException(status_code=402, detail=f'instance {model.__name__} with {id=} not found')
        # 2. получение image by image_id
        # image = await image_service.get_full_image(image_id)
        image = await image_service.get_image(image_id)
        return image
