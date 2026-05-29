# app.core.service.search_service.py
"""
    базовый класс для поиска
"""
from loguru import logger
from fastapi import Request
from typing import NamedTuple, Optional
from app.core.repositories.search_repository import SearchRepository
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.utils.fts_tokenizer import tokenized_string


class CleanedSearchQuery(NamedTuple):
    """
        сценарии для поиска
    """
    scenario: int
    fts_query: Optional[str] = None
    like_term: Optional[str] = None
    cursor: Optional[int] = None    # курсор для пагинации


class SearchService:
    @staticmethod
    def prepare_query(user_input: str, cursor: Optional[int] = None) -> Optional[CleanedSearchQuery]:
        """
        Анализирует строку ввода, очищает ее и определяет сценарий поиска.
        """
        if not user_input:
            return None

        # Проверяем наличие пробела на самом конце ДО очистки строки
        has_trailing_space = user_input.endswith(" ")

        # Очистка: оставляем только буквы, цифры и пробелы
        # clean_text = re.sub(r"[^\w\s]", "", user_input).strip()
        clean_text = tokenized_string(user_input)
        if not clean_text:
            return None

        words = clean_text.split()

        # Сценарий 1: Введено ровно одно слово (пробела на конце нет)
        if len(words) == 1 and not has_trailing_space:
            # Превращаем в префиксный FTS-запрос: 'слово':*
            return CleanedSearchQuery(scenario=1, fts_query=f"{words[0]}:*", cursor=cursor)

        # Сценарий 2: Несколько слов (или одно) с пробелом на конце
        if has_trailing_space:
            # Все слова превращаются в законченные токены через оператор &
            fts_query = " & ".join(f"{w}" for w in words)
            return CleanedSearchQuery(scenario=2, fts_query=fts_query, cursor=cursor)

        # Сценарий 3: Несколько слов без пробела на конце
        # Все слова кроме последнего уходят в FTS, последнее — фильтруется через LIKE в памяти
        fts_part = " & ".join(f"{w}" for w in words[:-1])
        like_part = words[-1]

        return CleanedSearchQuery(scenario=3, fts_query=fts_part, like_term=like_part, cursor=cursor)

    @classmethod
    async def search_items(cls, request: Request, search_str: str, limit: int,
                           repository: SearchRepository, model,
                           session: AsyncSession):
        """
            main method of search by fts index
        """
        query_data: CleanedSearchQuery | None = cls.prepare_query(search_str)
        result = await repository.search_all(query_data, model, session, limit)
        return result

    @classmethod
    async def search_items_keyset(
        cls, search_str: str, limit: int, cursor: Optional[int],  # Принимаем last_id от фронтенда
        repository: SearchRepository, model, session: AsyncSession
    ) -> dict:
        """ поиск со смещенимем по keyset"""

        query_data = cls.prepare_query(search_str, cursor=cursor)

        if not query_data:
            return {"ids": [], "next_cursor": None}

        # Вызываем репозиторий
        matching_ids = await repository.search_keyset(query_data, model, session, limit)

        # Формируем единый контракт ответа для Preact
        # Если это сценарий 1, следующим курсором будет последний ID.
        # Если сценарии 2-3, мы имитируем курсор (например, возвращаем искусственный маркер или ID)
        next_cursor = None
        if matching_ids:
            if query_data.scenario == 1:
                next_cursor = matching_ids[-1]
            else:
                # Для сценариев 2-3, если выдача полная (равна лимиту),
                # мы можем передать в качестве курсора порядковый номер элемента для имитации offset
                # Или передать ID последней записи, а репозиторий сам посчитает смещение
                next_cursor = matching_ids[-1]

        return {"ids": matching_ids, "next_cursor": next_cursor}
