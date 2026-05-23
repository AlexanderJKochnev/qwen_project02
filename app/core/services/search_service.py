# app.core.service.search_service.py
"""
    базовый класс для поиска
"""
import re
from loguru import logger
from fastapi import Request
from typing import NamedTuple, Optional
from app.core.repositories.search_repository import SearchRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils.fts_tokenizer import tokenizer


class CleanedSearchQuery(NamedTuple):
    scenario: int
    fts_query: Optional[str] = None
    like_term: Optional[str] = None


class SearchService:
    @staticmethod
    def prepare_query(user_input: str) -> Optional[CleanedSearchQuery]:
        """
        Анализирует строку ввода, очищает ее и определяет сценарий поиска.
        """
        if not user_input:
            return None

        # Проверяем наличие пробела на самом конце ДО очистки строки
        has_trailing_space = user_input.endswith(" ")

        # Очистка: оставляем только буквы, цифры и пробелы
        # clean_text = re.sub(r"[^\w\s]", "", user_input).strip()
        clean_text = tokenizer(user_input)
        if not clean_text:
            return None

        words = clean_text.split()

        # Сценарий 1: Введено ровно одно слово (пробела на конце нет)
        if len(words) == 1 and not has_trailing_space:
            # Превращаем в префиксный FTS-запрос: 'слово':*
            return CleanedSearchQuery(scenario=1, fts_query=f"{words[0]}:*")

        # Сценарий 2: Несколько слов (или одно) с пробелом на конце
        if has_trailing_space:
            # Все слова превращаются в законченные токены через оператор &
            fts_query = " & ".join(f"{w}" for w in words)
            return CleanedSearchQuery(scenario=2, fts_query=fts_query)

        # Сценарий 3: Несколько слов без пробела на конце
        # Все слова кроме последнего уходят в FTS, последнее — фильтруется через LIKE в памяти
        fts_part = " & ".join(f"{w}" for w in words[:-1])
        like_part = words[-1]

        return CleanedSearchQuery(scenario=3, fts_query=fts_part, like_term=like_part)

    @classmethod
    async def search_items(cls, request: Request, search_str: str, limit: int,
                           repository: SearchRepository, model,
                           session: AsyncSession):
        """
            main method of search by fts index
        """
        query_data: CleanedSearchQuery | None = cls.prepare_query(search_str)
        logger.warning(f'{query_data=}')
        result = await repository.search_all(query_data, model, session, limit)
        return result