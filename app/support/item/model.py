# app/support/Item/model.py

from __future__ import annotations
import json
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, UniqueConstraint, event, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.engine import Connection

from app.core.models.base_model import Base, BaseAt, ion, money, volume
from app.core.models.image_mixin import ImageMixin
from app.support.item.schemas import ItemReadRelation
from app.core.models.outbox import Outbox

if TYPE_CHECKING:
    from app.support.drink.model import Drink


class Item(Base, BaseAt, ImageMixin):
    __table_args__ = (UniqueConstraint('vol', 'drink_id', name='uq_items_unique'),)
    vol: Mapped[volume]  # объем тары
    price: Mapped[money]    # цена
    count: Mapped[ion]      # количество

    drink_id: Mapped[int] = mapped_column(ForeignKey("drinks.id"), nullable=False)
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


# Event listeners for transactional outbox
@event.listens_for(Item, 'after_insert')
def item_after_insert(mapper, connection, target):
    """Add INSERT operation to outbox after Item is inserted"""
    # Serialize the item to dictionary using its to_dict method
    item_dict = target.to_dict()
    
    # Convert the item to the schema format for search
    try:
        item_schema = ItemReadRelation.model_validate(item_dict)
        serialized_data = item_schema.model_dump(mode='json')
    except Exception:
        # Fallback to raw dict if validation fails
        serialized_data = item_dict
    
    # Insert outbox entry using raw SQL to avoid nested transactions
    connection.execute(
        Outbox.__table__.insert().values(
            entity_type='item',
            entity_id=target.id,
            operation='INSERT',
            payload=json.dumps(serialized_data),
            processed=False
        )
    )


@event.listens_for(Item, 'after_update')
def item_after_update(mapper, connection, target):
    """Add UPDATE operation to outbox after Item is updated"""
    # Serialize the item to dictionary using its to_dict method
    item_dict = target.to_dict()
    
    # Convert the item to the schema format for search
    try:
        item_schema = ItemReadRelation.model_validate(item_dict)
        serialized_data = item_schema.model_dump(mode='json')
    except Exception:
        # Fallback to raw dict if validation fails
        serialized_data = item_dict
    
    # Insert outbox entry using raw SQL to avoid nested transactions
    connection.execute(
        Outbox.__table__.insert().values(
            entity_type='item',
            entity_id=target.id,
            operation='UPDATE',
            payload=json.dumps(serialized_data),
            processed=False
        )
    )


@event.listens_for(Item, 'after_delete')
def item_after_delete(mapper, connection, target):
    """Add DELETE operation to outbox after Item is deleted"""
    # Insert outbox entry using raw SQL to avoid nested transactions
    connection.execute(
        Outbox.__table__.insert().values(
            entity_type='item',
            entity_id=target.id,
            operation='DELETE',
            payload=None,
            processed=False
        )
    )
