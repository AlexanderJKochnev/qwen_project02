from __future__ import annotations
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, TYPE_CHECKING, Type
from app.core.hash_norm import get_hashes_for_item


if TYPE_CHECKING:
    from app.support.drink.repository import DrinkRepository
    from app.support import Drink, Item


def extract_text_ultra_fast(data: Any, skip_keys: set = None) -> str:
    """
    извлекает текст из вложенного словаря и собирает в строку
    Ультра-быстрый вариант с минимальными проверками
    Использует генератор и быструю конкатенацию
    """
    if skip_keys is None:
        skip_keys = {'id', 'created_at', 'updated_at', 'deleted_at', 'version', 'is_deleted'}

    result = []

    def process(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if k not in skip_keys:
                    process(v)
        elif isinstance(value, list):
            for v in value:
                process(v)
        elif isinstance(value, str):
            if value and value.strip():
                # Замена переносов и табуляций
                v = value.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                # Схлопывание пробелов
                if '  ' in v:
                    v = ' '.join(v.split())
                result.append(v)
        elif isinstance(value, (int, float, bool)):
            result.append(str(value))

    process(data)
    return ' '.join(result)


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
    raw_text: str = extract_text_ultra_fast(drink_dict, skip_keys)
    
    instance.search_content = raw_text.lower()    # удалить после настройки word_hashes
    instance.word_hashes = get_hashes_for_item(raw_text)
    return instance
