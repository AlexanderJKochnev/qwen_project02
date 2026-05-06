# app/support/subregion/repository.py

from sqlalchemy import select
from sqlalchemy.orm import joinedload, load_only, selectinload

from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.core.utils.alchemy_utils import get_field_list
from app.support import Country, Drink, Item, Region, Site, Subregion


class SubregionRepository(Repository):
    model = Subregion

    @classmethod
    def get_item_drink(cls, id: int):
        return select(Item.id, Item.drink_id).where(
            Drink.id == Item.drink_id,
            Site.id == Drink.site_id,
            Site.subregion_id == id
        )

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Subregion).options(selectinload(Subregion.region).
                                         selectinload(Region.country))
        """
        return select(Subregion).options(
            selectinload(Subregion.region).selectinload(Region.country)
            )
        """
    @classmethod
    def get_short_query(cls, model: Subregion, field1: tuple = ('id', 'name', 'country_id', 'region_id')):
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
