# app.core.model.mixins.py
from typing import Optional
from sqlalchemy import Computed, Index, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import declared_attr, Mapped, mapped_column


class Search:
    """ поисковое поле для  """
    @declared_attr
    def search_content(cls) -> Mapped[Optional[str]]:
        return mapped_column(Text, deferred=True, nullable=True)

    @declared_attr
    def search_vector(cls):
        return mapped_column(
            TSVECTOR,
            Computed("to_tsvector('simple', coalesce(search_content, ''))", persisted=True)
        )

    @classmethod
    def __extra_constraints__(cls):
        """Обычный classmethod вместо declared_attr для безопасности события"""
        index_name = f"idx_{cls.__tablename__}_search_vector_gin"[:63]
        return [Index(index_name, "search_vector", postgresql_using="gin")]
