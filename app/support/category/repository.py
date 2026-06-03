# app/support/category/repository.py

from sqlalchemy import select
from app.core.repositories.sqlalchemy_repository import HandbookRepository
from app.support.item.model import Item
from app.support.drink.model import Drink
from app.support.subcategory.model import Subcategory
from app.support.category.model import Category
# CategoryRepository = RepositoryFactory.get_repository(Category)
# class CategoryRepository(Repository):
#    model = Category


class CategoryRepository(HandbookRepository):
    model = Category

    @classmethod
    def get_item_drink(cls, id: int):
        return select(Item.id, Item.drink_id).where(
            Drink.id == Item.drink_id,
            Subcategory.id == Drink.subcategory_id,
            Subcategory.category_id == id)
