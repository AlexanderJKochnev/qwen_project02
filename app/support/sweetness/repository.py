# app/support/sweetness/repository.py
from sqlalchemy import select

from app.support.sweetness.model import Sweetness
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository


class SweetnessRepository(Repository):
    model = Sweetness

    @classmethod
    def get_query_back(cls):
        """Returns a query to select Item IDs related to this model"""
        return select(Item.id).join(Drink, Item.drink_id == Drink.id).join(Sweetness, Drink.sweetness_id == Sweetness.id)
