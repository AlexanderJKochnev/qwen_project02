# app.support.parcel.repository.py
from sqlalchemy import exists, select
from sqlalchemy.orm import selectinload
from app.core.repositories.sqlalchemy_repository import Repository, ModelType
from app.support import Site, Drink, Item, Region, Subregion, Parcel


class ParcelRepository(Repository):
    model = Parcel

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.parcel_id == id
        )


class SiteRepository(Repository):
    model = Site

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.site_id == id
        )

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Site).options(
            selectinload(Site.subregion).selectinload(Subregion.region).selectinload(Region.country)
            )
