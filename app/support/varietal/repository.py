# app/support/varietal/repository.py
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.support.varietal.model import Varietal
from app.support.drink.model import DrinkVarietal, Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository, ModelType


# VarietalRepository = RepositoryFactory.get_repository(Varietal)
class VarietalRepository(Repository):
    model = Varietal

    @classmethod
    def get_query_back(cls):
        """Returns a query to select Item IDs related to this model"""
        return select(Item.id).join(Drink, Item.drink_id == Drink.id).join(DrinkVarietal, Drink.id == DrinkVarietal.drink_id).join(Varietal, DrinkVarietal.varietal_id == Varietal.id)

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(cls.model).options(selectinload(Varietal.drink_associations).joinedload(DrinkVarietal.drink))
