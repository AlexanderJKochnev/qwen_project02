# app/support/warehouse/model.py
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config.project_config import settings
from app.core.models.base_model import BaseFull, plural, str_null_true

if TYPE_CHECKING:
    from app.support.customer.model import Customer
    # from app.support.item.model import Item


class Warehouse(BaseFull):
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'warehouse'
    plural_name = plural(single_name)
    address: Mapped[str_null_true]
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)

    customer: Mapped["Customer"] = relationship(back_populates="warehouses", lazy="selectin")

    # items: Mapped[List["Item"]] = relationship("Item", back_populates=single_name,
    #                                            cascade=cascade,
    #                                            lazy=lazy)
