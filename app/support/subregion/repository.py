# app/support/subregion/repository.py

from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload
from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.support.region.model import Region
from app.support.subregion.model import Subregion


class SubregionRepository(Repository):
    model = Subregion

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.subregion_id == id
        )

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Subregion).options(selectinload(Subregion.region).
                                         selectinload(Region.country))
