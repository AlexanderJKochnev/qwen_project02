# app/support/subcategory/repository.py
from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload

from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support.subcategory.model import Subcategory
from app.support.item.model import Item
from app.support.drink.model import Drink


class SubcategoryRepository(Repository):
    model = Subcategory

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Subcategory).options(selectinload(Subcategory.category))

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.subcategory_id == id
        )
