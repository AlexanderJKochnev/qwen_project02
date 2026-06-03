# app/support/category/repository.py

from sqlalchemy import select
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.item.model import Item
from app.support.drink.model import Drink
from app.support.subcategory.model import Subcategory
from app.support.category.model import Category
from app.core.repositories.search_unaccent_repository import SearchRepositoryMixin
# CategoryRepository = RepositoryFactory.get_repository(Category)
# class CategoryRepository(Repository):
#    model = Category


class CategoryRepository(SearchRepositoryMixin, Repository):
    model = Category

    @classmethod
    def get_item_drink(cls, id: int):
        return select(Item.id, Item.drink_id).where(
            Drink.id == Item.drink_id,
            Subcategory.id == Drink.subcategory_id,
            Subcategory.category_id == id)
