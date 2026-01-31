# app/support/region/repository.py

from sqlalchemy import exists, select
from sqlalchemy.orm import selectinload

from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support.region.model import Region
from app.support.subregion.model import Subregion
from app.support.drink.model import Drink
from app.support.item.model import Item


class RegionRepository(Repository):
    model = Region

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Subregion.id == Drink.subregion_id,
            Subregion.region_id == id
        )

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Region).options(selectinload(Region.country))
