# app.core.model.mixins.py
from typing import Optional
from sqlalchemy import String, Index, func, text, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declared_attr, Mapped, mapped_column
from sqlalchemy.schema import Computed

# ---------------------------------------------------------
# ГЛАВНЫЙ СУПЕР-МИКСИН ДЛЯ АВТОМАТИЧЕСКОЙ СБОРКИ АРГУМЕНТОВ
# В МОДЕЛИ ИСПОЛЬЗУЮЩЕЙ МИСКСИНЫ НА ОСНВОЕ ЭТОГО
# ВАЖНО: Вместо __table_args__ пишем _local_table_args.
# Сюда пишем ТОЛЬКО локальные уникальные ключи этой конкретной модели.
# GeneralMixin сам заберет их, найдет индексы в SearchMixin и DynamicCompositeUniqueMixin,
# склеит всё вместе и правильно отдаст в SQLAlchemy.
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


# ---------------------------------------------------------
# МИКСИН 1: Одиночный уникальный индекс (lower + unaccent)
# ---------------------------------------------------------
class UniqueNormalizedNameMixin(GeneralMixin):
    """
    Автоматически добавляет уникальный функциональный индекс
    по нижнему регистру без диакритики для поля 'name'.
    """
    name: Mapped[str] = mapped_column(String, nullable=False)

    @classmethod
    def __extra_indices__(cls):
        index_name = f"uq_idx_{cls.__tablename__}_norm_name"[:63]
        return [
            Index(
                index_name,
                # func.unaccent(func.lower(text("name"))),
                func.public.immutable_unaccent(func.lower(text("name"))),
                unique=True
            )
        ]


# ---------------------------------------------------------
# МИКСИН 2: Динамический составной индекс (FK + lower + unaccent)
# ---------------------------------------------------------
class DynamicCompositeUniqueMixin(GeneralMixin):
    """
    Автоматически строит составной уникальный индекс по паре:
    [Динамическое поле связи] + [unaccent(lower(name))]
    применение
    class Drink(DynamicCompositeUniqueMixin, Base):
        __tablename__ = 'drinks'
        # Задаем параметр для миксина: составной индекс будет строиться с country_id
        __composite_fk_field__ = "country_id"

        country_id = Column(Integer, nullable=True) # Обычный ваш ForeignKey
        alcohol = Column(Integer)
    """
    name: Mapped[str] = mapped_column(String, nullable=True)

    @classmethod
    def __extra_indices__(cls):
        fk_field_name = getattr(cls, "__composite_fk_field__", None)
        if not fk_field_name:
            return []

        index_name = f"uq_idx_{cls.__tablename__}_{fk_field_name}_name"[:63]
        return [
            Index(
                index_name,
                text(fk_field_name),                          # Динамическое поле (например, country_id)
                # func.unaccent(func.lower(text("name"))),      # Нормализованное имя
                func.public.immutable_unaccent(func.lower(text("name"))),
                unique=True,
                postgresql_nulls_not_distinct=True            # Обработка NULL как идентичных (PG 15+)
            )
        ]
