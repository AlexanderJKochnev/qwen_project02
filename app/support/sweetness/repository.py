# app/support/sweetness/repository.py
from sqlalchemy import select

from app.support.sweetness.model import Sweetness
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository


class SweetnessRepository(Repository):
    model = Sweetness

    @classmethod
    def get_item_drink(cls, id: int):
        return select(Item.id, Item.drink_id).where(
            Drink.id == Item.drink_id,
            Drink.sweetness_id == id
        )
