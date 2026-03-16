# app/support/region/repository.py

from sqlalchemy import exists, select
from sqlalchemy.orm import selectinload

from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support import Site, Drink, Item, Region, Subregion


class RegionRepository(Repository):
    model = Region

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Site.id == Drink.site_id,
            Subregion.id == Site.subregion_id,
            Subregion.region_id == id
        )

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Region).options(selectinload(Region.country))
