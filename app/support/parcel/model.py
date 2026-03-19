# app.support.parcel.model.py
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.config.project_config import settings
from app.core.models.base_model import plural, BaseFullFree, BaseFull
from app.service_registry import registers_search_update


if TYPE_CHECKING:
    from app.support.subregion.model import Subregion


@registers_search_update("producer.drink.item")
class Parcel(BaseFull):
    """
        часть виноградника (верхняя, нижняя, возле леса - неуникальное имя)
    """
    lazy = settings.LAZY
    single_name = 'parcel'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
    # Обратная связь: many to one
    drinks = relationship(
        "Drink", back_populates=single_name, cascade=cascade, lazy=lazy
    )


# @registers_search_update("drink.item")
class Site(BaseFullFree):
    """
    виноградник в subregion
    """
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'site'
    plural_name = plural(single_name)
    subregion_id: Mapped[int] = mapped_column(ForeignKey("subregions.id"), nullable=False, index=True)
    subregion: Mapped["Subregion"] = relationship(back_populates=plural_name, lazy=lazy)
    drinks = relationship("Drink", back_populates=single_name,
                          cascade=cascade,
                          lazy=lazy)

    # __table_args__ = (UniqueConstraint('name', 'subregion_id', name='uq_site1_name_subregion'),)
    __table_args__ = (Index(
        "uq_  name_subregion_unique", "name", "subregion_id", unique=True, postgresql_nulls_not_distinct=True
        # Ключевой параметр
    ),)
