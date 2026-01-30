# app/support/supefood/repository.py
from sqlalchemy import select

from app.support.superfood.model import Superfood
from app.support.food.model import Food
from app.support.drink.model import DrinkFood, Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository


# SuperfoodRepository = RepositoryFactory.get_repository(Superfood)
# class SuperfoodRepository(Repository):
#    model = Superfood

class SuperfoodRepository(Repository):
    model = Superfood

    @classmethod
    def get_query_back(cls):
        """Returns a query to select Item IDs related to this model"""
        return select(Item.id).join(Drink, Item.drink_id == Drink.id).join(DrinkFood, Drink.id == DrinkFood.drink_id).join(Food, DrinkFood.food_id == Food.id).join(Superfood, Food.superfood_id == Superfood.id)
