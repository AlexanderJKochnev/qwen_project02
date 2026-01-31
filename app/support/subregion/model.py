# app/support/subregion/model.py
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import (Mapped, mapped_column, relationship)

from app.core.config.project_config import settings
from app.core.models.base_model import BaseFullFree, plural
from app.service_registry import registers_search_update

if TYPE_CHECKING:
    from app.support.country.model import Region


@registers_search_update("drink.item")
class Subregion(BaseFullFree):
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'subregion'
    plural_name = plural(single_name)
    region_id: Mapped[int] = mapped_column(ForeignKey("regions.id"), nullable=False, index=True)
    region: Mapped["Region"] = relationship(back_populates=plural_name, lazy=lazy)

    drinks = relationship("Drink", back_populates=single_name,
                          cascade=cascade,
                          lazy=lazy)
    # name: Mapped[str_null_false]
    __table_args__ = (UniqueConstraint('name', 'region_id', name='uq_subregion_name_region'),)
