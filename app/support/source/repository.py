# app.support.source.repositoory.py
from app.core.repositories.sqlalchemy_repository import Repository
# from app.support.item.model import Item
# from app.support.drink.model import Drink
from app.support.source.model import Source


class SourceRepository(Repository):
    model = Source