from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from typing import TYPE_CHECKING, Type
from app.core.utils.converters import extract_text_ultra_fast


if TYPE_CHECKING:
    from app.support.drink.repository import DrinkRepository
    from app.support import Drink, Item


async def reindex_items(instance: Item,
                        model: Type[Drink],
                        repository: DrinkRepository,
                        skip_keys: set, session: AsyncSession):
    """
        заполняет поле search_content текстовыми данными
    """
    drink_id: int = instance.drink_id
    # 0. получение drink
    drink = await repository.get_by_id(drink_id, model, session)
    drink_dict = drink.to_dict()
    result = extract_text_ultra_fast(drink_dict, skip_keys)
    instance.search_content = result.lower()
    return instance
