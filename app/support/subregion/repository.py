# app/support/subregion/repository.py

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.support.region.model import Region
from app.support.subregion.model import Subregion


class SubregionRepository(Repository):
    model = Subregion

    @classmethod
    def get_query_back(cls):
        """Returns a query to select Item IDs related to this model"""
        return select(Item.id).join(Drink, Item.drink_id == Drink.id).join(Subregion, Drink.subregion_id == Subregion.id)

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Subregion).options(selectinload(Subregion.region).
                                         selectinload(Region.country))
