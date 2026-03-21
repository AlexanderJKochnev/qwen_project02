# app/support/subcategory/repository.py
from sqlalchemy import select, exists
from sqlalchemy.orm import joinedload, load_only
from app.core.utils.alchemy_utils import get_field_list
from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support.subcategory.model import Subcategory
from app.support.category.model import Category
from app.support.item.model import Item
from app.support.drink.model import Drink


class SubcategoryRepository(Repository):
    model = Subcategory

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Subcategory).options(joinedload(Subcategory.category))

    @classmethod
    def get_short_query(cls, model: Subcategory, field1: tuple = ('id', 'name')):
        """
            Возвращает список модели только с нужными полями остальные None
            - использовать для list_view и вообще где только можно.
            для моделей с зависимостями - переопределить
        """

        fields = get_field_list(model, starts=field1)
        subcat = get_field_list(model, starts=field1)
        return select(model).options(joinedload(model.category).load_only(*subcat),
                                     load_only(*fields))

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.subcategory_id == id
        )
