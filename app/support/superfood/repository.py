# app/support/supefood/repository.py

from app.support.superfood.model import Superfood
from app.core.repositories.sqlalchemy_repository import HandbookRepository


# SuperfoodRepository = RepositoryFactory.get_repository(Superfood)
# class SuperfoodRepository(Repository):
#    model = Superfood

class SuperfoodRepository(HandbookRepository):
    model = Superfood
