# app.support.parcel.repository.py
from app.core.repositories.sqlalchemy_repository import Repository
# from app.support.item.model import Item
# from app.support.drink.model import Drink
from app.support.parcel.model import Parcel, Site


class ParcelRepository(Repository):
    model = Parcel

    """
    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Parcel.id == id
        )
    """


class SiteRepository(Repository):
    model = Site

    """
    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Site.id == id
        )
    """
