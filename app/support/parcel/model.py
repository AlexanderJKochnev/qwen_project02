# app.support.parcel.model.py
from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.config.project_config import settings
from app.core.models.base_model import BaseFull, plural, BaseFullFree
from app.service_registry import registers_search_update


if TYPE_CHECKING:
    from app.support.subregion.model import Subregion


# @registers_search_update("producer.drink.item")
class Parcel(BaseFullFree):
    """
        конфигурация vintage:
        последовтельно год за годом
        не последжовательно:  год через два-три
        одноразовый выпуск
    """
    lazy = settings.LAZY
    single_name = 'parcel'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
    subregion_id: Mapped[int] = mapped_column(ForeignKey("subregions.id"), nullable=False, index=True)
    subregion: Mapped["Subregion"] = relationship(back_populates=plural_name, lazy=lazy)
    # Обратная связь: many to one
    # drinks = relationship(
    #     "Drink", back_populates=single_name, cascade=cascade, lazy=lazy
    #     )
    __table_args__ = (UniqueConstraint('name', 'subregion_id', name='uq_site_name_subregion'),)


@registers_search_update("drink.item")
class Site(BaseFull):
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'site'
    plural_name = plural(single_name)
    subregion_id: Mapped[int] = mapped_column(ForeignKey("subregions.id"), nullable=False, index=True)
    subregion: Mapped["Subregion"] = relationship(back_populates=plural_name, lazy=lazy)

    drinks = relationship("Drink", back_populates=single_name,
                          cascade=cascade,
                          lazy=lazy)
