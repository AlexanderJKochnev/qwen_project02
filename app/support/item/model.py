# app/support/Item/model.py

from __future__ import annotations
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
# from sqlalchemy.engine import Connection
# from sqlalchemy.sql import Table

from app.core.models.base_model import Base, BaseAt, ion, money, volume, Search
from app.core.models.image_mixin import ImageMixin


if TYPE_CHECKING:
    from app.support.drink.model import Drink


class Item(Base, BaseAt, ImageMixin, Search):
    __table_args__ = (UniqueConstraint('vol', 'drink_id', name='uq_items_unique'),
                      Index('idx_items_fts', 'search_vector', postgresql_using='gin')
                      )

    vol: Mapped[volume]  # объем тары
    price: Mapped[money]    # цена
    count: Mapped[ion]      # количество

    drink_id: Mapped[int] = mapped_column(ForeignKey("drinks.id"), nullable=False, index=True)
    # warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), nullable=True)

    # warehouse: Mapped["Warehouse"] = relationship(back_populates="items")
    drink: Mapped["Drink"] = relationship(back_populates="items")

    def __str__(self):
        # переоопределять в особенных формах
        return f'{self.drink.__str__()}, {self.vol / 100:.2%} %'
        # f"{number/100:.2%} " (54.34% = 0.5434)

    def __repr__(self):
        # return f"<Category(name={self.name})>"
        return str(self)
