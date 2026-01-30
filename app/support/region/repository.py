# app/support/region/repository.py

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support.region.model import Region
from app.support.subregion.model import Subregion
from app.support.drink.model import Drink
from app.support.item.model import Item


class RegionRepository(Repository):
    model = Region

    @classmethod
    def get_query_back(cls, id):
        """Returns a query to select Item IDs related to this model"""
        return (select(Item.id)
                .join(Item.drink)
                .join(Drink.subregion)
                .where(Subregion.region_id == id))

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Region).options(selectinload(Region.country))
