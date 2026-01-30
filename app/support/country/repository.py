# app/support/country/repository.py
from sqlalchemy import select

from app.support.country.model import Country
from app.support.region.model import Region
from app.support.subregion.model import Subregion
from app.support.drink.model import Drink
from app.support.item.model import Item
from app.core.repositories.sqlalchemy_repository import Repository


class CountryRepository(Repository):
    model = Country

    @classmethod
    def get_query_back(cls, id: int):
        """Returns a query to select Item IDs related to this model"""
        return (select(Item.id).join(Item.drink)
                .join(Drink.subregion)
                .join(Subregion.region)
                .where(Region.country_id == id))
