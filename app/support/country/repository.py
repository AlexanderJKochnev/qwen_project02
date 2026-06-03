# app/support/country/repository.py
from sqlalchemy import select
from app.core.repositories.sqlalchemy_repository import HandbookRepository
from app.support import Site, Drink, Item, Region, Subregion, Country


class CountryRepository(HandbookRepository):
    model = Country

    @classmethod
    def get_item_drink(cls, id: int):
        return select(Item.id, Item.drink_id).where(
            Drink.id == Item.drink_id,
            Site.id == Drink.site_id,
            Subregion.id == Site.subregion_id,
            Region.id == Subregion.region_id,
            Region.country_id == id
        )
