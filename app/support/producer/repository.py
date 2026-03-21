# app/support/producer/repository.py
# from sqlalchemy import select, exists
from sqlalchemy import select, exists
from sqlalchemy.orm import joinedload, load_only
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.utils.alchemy_utils import get_field_list
from app.support.producer.model import Producer, ProducerTitle
from app.support import Drink, Item


class ProducerTitleRepository(Repository):
    model = ProducerTitle

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.producer_id == Producer.id,
            Producer.producertitle_id == id
        )


class ProducerRepository(Repository):
    model = Producer

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.producer_id == id
        )

    @classmethod
    def get_query(cls, model: Producer):
        # Добавляем загрузку связи с relationships
        return select(Producer).options(joinedload(Producer.producertitle))

    @classmethod
    def get_short_query(cls, model: Producer, field1: tuple = ('id', 'name', 'producertitle_id')):
        """
            Возвращает список модели только с нужными полями остальные None
            - использовать для list_view и вообще где только можно.
            для моделей с зависимостями - переопределить
        """

        fields = get_field_list(model, starts=field1)
        subcat = get_field_list(ProducerTitle, starts=field1)
        return select(model).options(load_only(*fields))
        # return select(model).options(
        #     joinedload(model.producertitle).load_only(*subcat), load_only(*fields)
        # )
