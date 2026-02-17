# app/support/food/repository.py
from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload
from app.support.food.model import Food
from app.support.drink.model import DrinkFood, Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.types import ModelType


# FoodRepository = RepositoryFactory.get_repository(Food)
class FoodRepository(Repository):
    model = Food

    @classmethod
    def item_exists(cls, id: int):
        """
        good for update or delete
        """
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.id == DrinkFood.drink_id,
            DrinkFood.food_id == id
        )

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Food).options(selectinload(Food.drink_associations).joinedload(DrinkFood.drink))
