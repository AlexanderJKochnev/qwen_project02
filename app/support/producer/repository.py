# app/support/producer/repository.py
# from sqlalchemy import select, exists
from app.core.repositories.sqlalchemy_repository import Repository
# from app.support.item.model import Item
# from app.support.drink.model import Drink
from app.support.producer.model import Producer, ProducerTitle


class ProducerTitleRepository(Repository):
    model = ProducerTitle

    """
    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Producer.id == Drink.producer_id,
            Producer.producertitle_id == id
        )
    """


class ProducerRepository(Repository):
    model = Producer

    """
    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Producer.id == Drink.producer_id,
            Producer.producertitle_id == id
        )
    """
