# app/support/varietal/repository.py
from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload
from app.support.varietal.model import Varietal
from app.support.drink.model import DrinkVarietal, Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository, ModelType


# VarietalRepository = RepositoryFactory.get_repository(Varietal)
class VarietalRepository(Repository):
    model = Varietal

    @classmethod
    def item_exists(cls, id: int):
        """
        good for update or delete
        """
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.id == DrinkVarietal.drink_id,
            DrinkVarietal.varietal_id == id
        )

    @classmethod
    def get_query_back(cls, id: int):
        """ Returns a query to select Item IDs related to this model
             just for memory
        """
        return (select(Item.id)
                .join(Item.drink)
                .join(Drink.varietal_associations)
                .where(DrinkVarietal.varietal_id == id))

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(cls.model).options(selectinload(Varietal.drink_associations).joinedload(DrinkVarietal.drink))
