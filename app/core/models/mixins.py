# app.core.model.mixins.py
from typing import Optional
from sqlalchemy import Computed, Index, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declared_attr, Mapped, mapped_column


# ---------------------------------------------------------
# ГЛАВНЫЙ СУПЕР-МИКСИН ДЛЯ АВТОМАТИЧЕСКОЙ СБОРКИ АРГУМЕНТОВ
# ---------------------------------------------------------
class GeneralMixin:
    """
    Базовый миксин, который избавляет от костылей.
    Он автоматически собирает все индексы из методов __extra_indices__
    всех унаследованных миксинов и склеивает их с локальными аргументами модели.
    """

    @declared_attr.directive
    def __table_args__(cls):
        # 1. Собираем локальные аргументы, если они объявлены в самой модели под именем _local_table_args
        local_args = getattr(cls, "_local_table_args", ())
        if isinstance(local_args, tuple):
            local_args = list(local_args)
        elif isinstance(local_args, dict):
            local_args = [local_args]
        else:
            local_args = [local_args]

        # 2. Автоматически собираем индексы из всех родительских миксинов по MRO
        mixin_args = []
        for base in cls.__mro__:
            # Ищем наш кастомный метод сборки индексов в миксинах
            if "__extra_indices__" in base.__dict__:
                method = base.__dict__["__extra_indices__"]
                if isinstance(method, classmethod):
                    method = method.__func__
                if callable(method):
                    mixin_args.extend(method(cls))

        # Возвращаем единый кортеж для SQLAlchemy — без дубликатов и костылей
        final_args = []
        for arg in (local_args + mixin_args):
            if arg not in final_args:
                final_args.append(arg)

        return tuple(final_args)


class Search(GeneralMixin):
    """ поисковое поле для  """
    """Миксин полнотекстового поиска (FTS)"""

    @declared_attr
    def search_content(cls) -> Mapped[Optional[str]]:
        return mapped_column(Text, deferred=True, nullable=True)

    @declared_attr
    def search_vector(cls):
        return mapped_column(
            TSVECTOR, Computed("to_tsvector('simple', coalesce(search_content, ''))", persisted=True)
        )

    @classmethod
    def __extra_indices__(cls):
        # Передаем строку имени столбца — теперь Alembic увидит её идеально
        return [Index(f"idx_{cls.__tablename__}_search_vector_gin", "search_vector", postgresql_using="gin")]

    @classmethod
    def __extra_constraints__(cls):
        """Обычный classmethod вместо declared_attr для безопасности события"""
        index_name = f"idx_{cls.__tablename__}_search_vector_gin"[:63]
        return [Index(index_name, "search_vector", postgresql_using="gin")]
