# app/support/subcategory/model.py
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config.project_config import settings
from app.core.models.base_model import BaseFullFree, plural
from app.service_registry import registers_search_update

if TYPE_CHECKING:
    from app.support.category.model import Category


@registers_search_update("drinks.items")
class Subcategory(BaseFullFree):

    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'subcategory'
    plural_name = plural(single_name)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    category: Mapped["Category"] = relationship(back_populates=plural_name, lazy=lazy)
    drinks = relationship("Drink", back_populates=single_name,
                          cascade=cascade,
                          lazy=lazy)
    # name: Mapped[str_null_true]
    __table_args__ = (UniqueConstraint('name', 'category_id', name='uq_subcategory_name_category'),)
