# app/support/country/repository.py
from sqlalchemy import exists

from app.support.country.model import Country
from app.support.region.model import Region
from app.support.subregion.model import Subregion
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository


class CountryRepository(Repository):
    model = Country

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Subregion.id == Drink.subregion_id,
            Region.id == Subregion.region_id,
            Region.country_id == id
        )
