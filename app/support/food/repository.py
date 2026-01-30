# app/support/food/repository.py
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.support.food.model import Food
from app.support.drink.model import DrinkFood, Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository, ModelType


# FoodRepository = RepositoryFactory.get_repository(Food)
class FoodRepository(Repository):
    model = Food

    @classmethod
    def get_query_back(cls, id: int):
        """Returns a query to select Item IDs related to this model"""
        return (select(Item.id)
                .join(Item.drink)
                .join(Drink.food_associations)  # Используем Mapped[List["DrinkFood"]]
                .where(DrinkFood.food_id == id))

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Food).options(selectinload(Food.drink_associations).joinedload(DrinkFood.drink))
