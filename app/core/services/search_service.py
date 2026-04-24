# app.core.service.search_service.py
"""
    поиск по всем текстовым полям с начала слова по всем связанным таблицам вверх
"""
from collections.abc import Sequence
from typing import Any, List, Optional, Set, Type, TypeVar

from sqlalchemy import or_, select, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import class_mapper, DeclarativeBase, selectinload

T = TypeVar('T', bound=DeclarativeBase)


class DeepSearchBuilder:
    """
    билдер для построения поисковых запросов

    пример использования
    results = await (
            DeepSearchBuilder(session)
            .search("John")
            .depth(2)
            .limit(10)
            .order_by(model.name)
            .eager_load(True)
            .execute(model)
        )
    возвращает result.scalars().all()
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self._search_term: Optional[str] = None
        self._max_depth: int = 1
        self._visited_models: Set[str] = set()
        self._conditions: List[Any] = []
        self._order_by: List[Any] = []
        self._limit: Optional[int] = None
        self._offset: Optional[int] = None
        self._eager_load: bool = True

    def search(self, term: str) -> 'DeepSearchBuilder':
        """Устанавливает поисковый термин"""
        self._search_term = term
        return self

    def depth(self, max_depth: int) -> 'DeepSearchBuilder':
        """Устанавливает максимальную глубину поиска"""
        self._max_depth = max_depth
        return self

    def limit(self, limit: int) -> 'DeepSearchBuilder':
        """Устанавливает лимит результатов"""
        self._limit = limit
        return self

    def offset(self, offset: int) -> 'DeepSearchBuilder':
        """Устанавливает смещение"""
        self._offset = offset
        return self

    def order_by(self, *fields) -> 'DeepSearchBuilder':
        """Устанавливает сортировку"""
        self._order_by.extend(fields)
        return self

    def eager_load(self, enabled: bool = True) -> 'DeepSearchBuilder':
        """Включает/отключает жадную загрузку связей"""
        self._eager_load = enabled
        return self

    def _build_string_conditions(self, model: Type[T]) -> List[Any]:
        """Строит условия поиска по текстовым полям"""
        conditions = []
        mapper = class_mapper(model)

        for column in mapper.columns:
            if isinstance(column.type, String):
                conditions.append(column.ilike(f'{self._search_term}%'))

        return conditions

    async def _build_relationship_conditions(
            self, model: Type[T], current_depth: int
    ) -> List[Any]:
        """Асинхронно строит условия по связям"""
        if current_depth >= self._max_depth or not self._search_term:
            return []

        conditions = []
        mapper = class_mapper(model)
        model_key = f"{model.__module__}.{model.__name__}"

        if model_key in self._visited_models:
            return []

        self._visited_models.add(model_key)

        for relationship in mapper.relationships:
            related_model = relationship.mapper.class_

            # Пропускаем self-referential на максимальной глубине
            if related_model == model and current_depth + 1 >= self._max_depth:
                continue

            # Рекурсивно строим подзапрос
            sub_builder = DeepSearchBuilder(self.session)
            sub_builder.search(self._search_term).depth(self._max_depth - current_depth - 1)
            sub_builder._visited_models = self._visited_models.copy()

            sub_filter = await sub_builder._build_filter(
                related_model, current_depth + 1
            )

            if sub_filter is not None:
                # Создаем EXISTS подзапрос для проверки существования
                subquery = select(related_model).where(sub_filter)

                if relationship.uselist:
                    # Для коллекций используем any()
                    conditions.append(
                        getattr(model, relationship.key).any(
                            related_model.id.in_(subquery.subquery())
                        )
                    )
                else:
                    # Для одиночных связей используем has()
                    conditions.append(
                        getattr(model, relationship.key).has(
                            related_model.id.in_(subquery.subquery())
                        )
                    )

        return conditions

    async def _build_filter(self, model: Type[T], current_depth: int = 0) -> Optional[Any]:
        """Основной метод построения фильтра"""
        if not self._search_term:
            return None

        all_conditions = []

        # Добавляем условия по текстовым полям
        all_conditions.extend(self._build_string_conditions(model))

        # Добавляем условия по связям
        relationship_conditions = await self._build_relationship_conditions(model, current_depth)
        all_conditions.extend(relationship_conditions)

        return or_(*all_conditions) if all_conditions else None

    async def execute(self, model: Type[T]) -> Sequence[T]:
        """Выполняет поиск и возвращает результаты"""
        if not self._search_term:
            return []

        # Строим фильтр
        filter_condition = await self._build_filter(model)

        if filter_condition is None:
            return []

        # Строим запрос
        query = select(model).where(filter_condition)

        # Добавляем пагинацию
        if self._limit:
            query = query.limit(self._limit)
        if self._offset:
            query = query.offset(self._offset)

        # Добавляем сортировку
        if self._order_by:
            query = query.order_by(*self._order_by)

        # Добавляем жадную загрузку связей
        if self._eager_load and self._max_depth > 0:
            query = self._add_selectinloads(query, model, self._max_depth)

        # Выполняем запрос
        result = await self.session.execute(query)
        return result.scalars().all()

    def _add_selectinloads(self, query: Any, model: Type[T], depth: int, current: int = 0) -> Any:
        """Добавляет selectinload для оптимизации запросов"""
        if current >= depth:
            return query

        mapper = class_mapper(model)

        for relationship in mapper.relationships:
            rel_key = relationship.key

            if current + 1 < depth:
                # Для nested связей используем selectinload рекурсивно
                # Примечание: полная поддержка nested selectinload требует более сложной реализации
                query = query.options(selectinload(rel_key))
            else:
                query = query.options(selectinload(rel_key))
        return query
