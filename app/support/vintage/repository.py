# app.support.vintage.repository.py
from sqlalchemy import select
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.item.model import Item
from app.support.drink.model import Drink
from app.support.vintage.model import VintageConfig, Classification, Designation


class VintageConfigRepository(Repository):
    model = VintageConfig

    @classmethod
    def get_item_drink(cls, id: int):
        return select(Item.id, Item.drink_id).where(
            Drink.id == Item.drink_id,
            Drink.vintageconfig_id == id
        )


class ClassificationRepository(Repository):
    model = Classification

    @classmethod
    def get_item_drink(cls, id: int):
        return select(Item.id, Item.drink_id).where(
            Drink.id == Item.drink_id,
            Drink.classification_id == id
        )


class DesignationRepository(Repository):
    model = Designation

    @classmethod
    def get_item_drink(cls, id: int):
        return select(Item.id, Item.drink_id).where(
            Drink.id == Item.drink_id,
            Drink.designation_id == id
        )
