# app/support/category/repository.py

from sqlalchemy import select
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.item.model import Item
from app.support.drink.model import Drink
from app.support.subcategory.model import Subcategory
from app.support.category.model import Category
# CategoryRepository = RepositoryFactory.get_repository(Category)
# class CategoryRepository(Repository):
#    model = Category


class CategoryRepository(Repository):
    model = Category

    @classmethod
    def get_query_back(cls, category_id: int):
        """ получаем список Item.id """
        return (select(Item.id).join(Item.drink)  # SQLAlchemy сама поймет связь, если есть ForeignKey
                               .join(Drink.subcategory).where(Subcategory.category_id == category_id))
