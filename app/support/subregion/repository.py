# app/support/subregion/repository.py

from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload
from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support import Site, Drink, Item, Region, Subregion


class SubregionRepository(Repository):
    model = Subregion

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Site.id == Drink.site_id,
            Site.subregion_id == id
        )

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Subregion).options(selectinload(Subregion.region).
                                         selectinload(Region.country))
