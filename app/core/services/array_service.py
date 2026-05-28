# app.core.service.array_service.py
from typing import Any, Dict, List
from random import randint
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, Request
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.types import ModelType
from app.core.repositories.array_repository import ArrayRepository
from app.core.services.seaweed_service import SeaweedsService
from app.core.utils.alchemy_utils import has_column
from app.core.utils.common_utils import jprint
from app.core.utils.image_utils import get_default_image
from app.core.utils.io_utils import get_font_list
from app.core.utils.pillow_generator import TextConfig, generate_text_image, TextConfigAdaptive
from app.core.utils.color_palette import auto_match_colors_old, GeneratedPalette, auto_match_colors


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
                                 session: AsyncSession,
                                 block: int = 2) -> Dict[str, Any]:
        """ Удаление элемента по индексу """
        result = await repository.del_by_index_array(id, pos, model, arrayName, session, block)
        return {'arrray': result, 'size': len(result) if result else 0}

    @classmethod
    async def swap_by_index_array(cls, id: int, pos1: int, pos2: int,
                                  model: ModelType, arrayName: str,
                                  repository: ArrayRepository,
                                  session: AsyncSession, block: int = 2) -> Dict[str, Any]:
        """ Поменять два элемента местами """
        result = await repository.swap_by_index_array(id, pos1, pos2, model, arrayName, session, block)
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
            cls, request: Request, id: int, repository: Repository, model: ModelType, session: AsyncSession,
            image_service: SeaweedsService, pos: int = 0
    ) -> bytes:
        """
            получение полноразмерного изображения по id напитка
        """
        #  ПОИСК КОЛОНКИ seaweed_fids
        arrayColname = 'seaweed_fids'
        if not has_column(model, arrayColname):
            raise HTTPException(status_code=422, detail=f'{model.__name__} model has no images at all')
        # 1. получение image_id by id
        image_id = await cls.get_item_of_array_by_id(id, model, arrayColname, repository, session, pos)
        if not image_id:
            # image_id = get_default_image(request, pos)
            image: bytes = await cls.generate_random_image_by_id(id, session, False)
            return image
        # 2. получение image by image_id
        # image = await image_service.get_full_image(image_id)
        image: bytes = await image_service.get_image(image_id)
        return image

    @classmethod
    async def test_generate_image_by_text(
            cls, request: Request, id, preset: dict, session: AsyncSession
    ) -> bytes:
        """
            тестирование изображений
        """
        instance = await cls.repository.get_by_id(id, cls.model, session)
        item_dict: dict = instance.to_dict_fast()
        drink_dict = item_dict.get('drink')
        if not drink_dict:
            return None
        txt = drink_dict.get("diplay_name", f"{drink_dict.get("title")} {drink_dict.get("subtitle")}")
        preset['text'] = txt
        config = TextConfig(**preset)
        result: bytes = generate_text_image(config, "WEBP", 100)
        return result

    @classmethod
    async def test_generate_image_by_background(
            cls, request: Request, id, preset: dict, session: AsyncSession
    ) -> bytes:
        """
            тестирование изображений
            автоподбор цвета по цвету подложки
        """
        instance = await cls.repository.get_by_id(id, cls.model, session)
        item_dict: dict = instance.to_dict_fast()
        drink_dict = item_dict.get('drink')
        if not drink_dict:
            return None
        txt = drink_dict.get("display_name", f"{drink_dict.get('title')} {drink_dict.get('subtitle')}")
        preset['text'] = txt
        palette: GeneratedPalette = auto_match_colors(preset.get("background_color"))
        preset["fill_color"] = palette.fill_color
        preset["stroke_color"] = palette.stroke_color
        preset["shadow_color"] = palette.shadow_color
        config = TextConfig(**preset)
        result: bytes = generate_text_image(config, "WEBP", 100)
        return result

    @classmethod
    async def generate_image_by_id(
            cls, id: int, font: str, session: AsyncSession, bg_opacity: int = 255
    ) -> bytes:
        """
            генерация рисунка по тексту с адаптивной цветовой палитрой - старый метод
        """
        instance = await cls.repository.get_by_id(id, cls.model, session)
        item_dict: dict = instance.to_dict_fast()
        drink_dict = item_dict.get('drink')
        # get txt
        if not drink_dict:
            return None
        txt = drink_dict.get("display_name", f"{drink_dict.get('title')} {drink_dict.get('subtitle')}")
        # get back color
        if subcategory := drink_dict.get('subcategory'):
            category: dict = subcategory.get('category')
            background_color = subcategory.get('color', category.get('color', "#FFFFFF"))
        else:
            background_color = "#FFFFFF"
        palette: GeneratedPalette = auto_match_colors_old(background_color)
        logger.warning(f'{palette=}')
        preset: dict = {}
        preset["text"] = txt
        preset["font_path"] = font
        preset["background_color"] = background_color
        preset["background_opacity"] = bg_opacity
        preset["fill_color"] = palette.fill_color
        preset["stroke_color"] = palette.stroke_color
        preset["shadow_color"] = palette.shadow_color
        config = TextConfig(**preset)
        result: bytes = generate_text_image(config, "WEBP", 100)
        return result

    @classmethod
    async def test_generate_by_id(
            cls, request: Request, id: int, font: str, session: AsyncSession
    ) -> bytes:
        return await cls.generate_image_by_id(id, font, session)

    @classmethod
    async def generate_image_by_id_v2(
            cls, id: int, font: str, session: AsyncSession, bg_opacity: int = 255
    ) -> bytes:
        """
            генерация рисунка по тексту с адаптивной цветовой палитрой - новый метод
        """
        instance = await cls.repository.get_by_id(id, cls.model, session)
        item_dict: dict = instance.to_dict_fast()
        drink_dict = item_dict.get('drink')
        # get txt
        if not drink_dict:
            return None
        txt = drink_dict.get("display_name", f"{drink_dict.get('title')} {drink_dict.get('subtitle')}")
        # get back color
        if subcategory := drink_dict.get('subcategory'):
            category: dict = subcategory.get('category')
            background_color = subcategory.get('color', category.get('color', "#FFFFFF"))
        else:
            background_color = "#FFFFFF"
        preset: dict = {}
        preset["text"] = txt
        preset["font_path"] = font
        preset["background_color"] = background_color
        config = TextConfigAdaptive(**preset)
        logger.warning(f'{config=}')
        result: bytes = generate_text_image(config, "WEBP", 100)
        return result

    @classmethod
    async def generate_random_image_by_id(cls, id: int, session: AsyncSession, bg_opacity: bool) -> bytes:
        """
            генерация рисунка с рандомными шрифтами и адаптивной цветовой палитрой
        """
        # получение шрифтов
        font_list = get_font_list('fonts')
        x = len(font_list)
        rx = randint(0, x - 1)
        font = font_list[rx]
        return await cls.generate_image_by_id_v2(id, font, session, bg_opacity)
