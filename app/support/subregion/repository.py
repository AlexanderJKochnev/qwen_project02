# app/support/subregion/repository.py

from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload, joinedload, load_only

from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.core.utils.alchemy_utils import get_field_list
from app.support import Site, Drink, Item, Region, Subregion, Country


class SubregionRepository(Repository):
    model = Subregion

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Site.id == Drink.site_id,
            Site.subregion_id == id
        )

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Subregion).options(selectinload(Subregion.region).
                                         selectinload(Region.country))

    @classmethod
    def get_short_query(cls, model: Region, field1: tuple = ('id', 'name', 'country_id', 'region_id')):
        """
            Возвращает список модели только с нужными полями остальные None
            - использовать для list_view и вообще где только можно.
            для моделей с зависимостями - переопределить
        """

        fields = get_field_list(model, starts=field1)
        subcat = get_field_list(Country, starts=field1)
        tier3 = get_field_list(Region, starts=field1)
        return select(model).options(
            joinedload(model.region).load_only(*tier3).joinedload(Region.country).load_only(*subcat),
            load_only(*fields)
        )
