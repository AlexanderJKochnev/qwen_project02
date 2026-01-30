# app/support/subcategory/repository.py
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.support.subcategory.model import Subcategory


class SubcategoryRepository(Repository):
    model = Subcategory

    @classmethod
    def get_query_back(cls):
        """Returns a query to select Item IDs related to this model"""
        return select(Item.id).join(Drink, Item.drink_id == Drink.id).join(Subcategory, Drink.subcategory_id == Subcategory.id)

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Subcategory).options(selectinload(Subcategory.category))
