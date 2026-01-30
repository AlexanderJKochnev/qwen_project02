# app/support/sweetness/repository.py
from sqlalchemy import select

from app.support.sweetness.model import Sweetness
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository


class SweetnessRepository(Repository):
    model = Sweetness

    @classmethod
    def get_query_back(cls, id: int):
        """Returns a query to select Item IDs related to this model"""
        return (select(Item.id)
                .join(Item.drink)
                .where(Drink.sweetness_id == id))