# app/support/region/model.py
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import (Mapped, mapped_column, relationship)

from app.core.config.project_config import settings
from app.core.models.base_model import BaseFullFree, plural, str_null_false
from app.service_registry import registers_search_update

if TYPE_CHECKING:
    from app.support.country.model import Country


@registers_search_update("subregion.site.drink.item")
class Region(BaseFullFree):
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single = 'region'
    plural_name = plural(single)
    name: Mapped[str_null_false]
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"), nullable=False, index=True)
    country: Mapped["Country"] = relationship(back_populates=plural_name, lazy=lazy)

    subregions = relationship("Subregion", back_populates=single,
                              cascade=cascade,
                              lazy=lazy)
    # __table_args__ = (UniqueConstraint('name', 'country_id', name='uq_region_name_country'),)

    __table_args__ = (
        Index("uq_  name_country_unique", "name", "country_id", unique=True,
              postgresql_nulls_not_distinct=True  # Ключевой параметр
              ),
    )
