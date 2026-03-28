from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import ModelType
from app.core.utils.converters import extract_text_ultra_fast
from app.support import Drink, Item
from app.support.drink.repository import DrinkRepository


async def reindex_items(instance: Item, skip_keys, session: AsyncSession) -> ModelType:
    """
        заполняет поле search_content текстовыми данными
    """
    drink_id: int = instance.drink_id
    # 0. получение drink
    drink: Drink = await DrinkRepository.get_by_id(drink_id, Drink, session)
    drink_dict = drink.to_dict()
    result = extract_text_ultra_fast(drink_dict, skip_keys)
    instance.search_content = result.lower()
    return instance
