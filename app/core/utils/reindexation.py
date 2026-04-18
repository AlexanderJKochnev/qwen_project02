# app.core.utils.reindexation.py
from __future__ import annotations
from array import array
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, TYPE_CHECKING, Type
from app.core.hash_norm import get_hashes_for_item


if TYPE_CHECKING:
    from app.support.drink.repository import DrinkRepository
    from app.support import Drink, Item


def extract_text_optimized(data: dict, skip_keys: set = None) -> str:
    """
    Оптимизированная версия для больших данных
    Работает напрямую со словарем без рекурсии
    """
    if skip_keys is None:
        skip_keys = {'id', 'created_at', 'updated_at', 'deleted_at', 'version', 'is_deleted'}

    result_parts = []
    stack = [data]

    while stack:
        current = stack.pop()

        if isinstance(current, dict):
            for k, v in current.items():
                if k not in skip_keys:
                    stack.append(v)
        elif isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, str):
            if current and current.strip():
                # Быстрая замена символов
                if '\n' in current or '\r' in current or '\t' in current:
                    current = current.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
                if '  ' in current:
                    current = ' '.join(current.split())
                result_parts.append(current)
        elif isinstance(current, (int, float, bool)):
            result_parts.append(str(current))

    return ' '.join(result_parts)


def extract_text_fastest(data: dict, skip_keys: set = None) -> str:
    """Максимально быстрая версия с минимальными проверками"""
    if skip_keys is None:
        skip_keys = {'id', 'created_at', 'updated_at', 'deleted_at', 'version', 'is_deleted'}

    result = []
    stack = [data]

    while stack:
        current = stack.pop()

        if isinstance(current, dict):
            # Быстрый обход без проверки ключей на каждом уровне
            for k, v in current.items():
                if k not in skip_keys:
                    if isinstance(v, (dict, list)):
                        stack.append(v)
                    elif isinstance(v, str) and v:
                        # Убираем лишние пробелы и переносы
                        result.append(v.replace('\n', ' ').replace('\r', ' ').replace('\t', ' '))
                    elif isinstance(v, (int, float, bool)):
                        result.append(str(v))
        elif isinstance(current, list):
            stack.extend(current)

    # Финальная обработка
    text = ' '.join(result)
    if '  ' in text:
        text = ' '.join(text.split())
    return text


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
