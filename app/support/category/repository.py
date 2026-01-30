# app/support/category/repository.py
from sqlalchemy import select

from app.support.category.model import Category
from app.support.subcategory.model import Subcategory
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository


# CategoryRepository = RepositoryFactory.get_repository(Category)
# class CategoryRepository(Repository):
#    model = Category

class CategoryRepository(Repository):
    model = Category

    @classmethod
    def get_query_back(cls):
        """Returns a query to select Item IDs related to this model"""
        return select(Item.id).join(Drink, Item.drink_id == Drink.id).join(Subcategory, Drink.subcategory_id == Subcategory.id).join(Category, Subcategory.category_id == Category.id)
