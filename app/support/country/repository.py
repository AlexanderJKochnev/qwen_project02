# app/support/country/repository.py
from sqlalchemy import exists

from app.core.repositories.sqlalchemy_repository import Repository
from app.support import Site, Drink, Item, Region, Subregion, Country


class CountryRepository(Repository):
    model = Country

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Site.id == Drink.site_id,
            Subregion.id == Site.subregion_id,
            Region.id == Subregion.region_id,
            Region.country_id == id
        )
