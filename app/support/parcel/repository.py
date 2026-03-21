# app.support.parcel.repository.py
from sqlalchemy import exists, select
from sqlalchemy.orm import selectinload, joinedload, load_only
from app.core.repositories.sqlalchemy_repository import Repository, ModelType
from app.core.utils.alchemy_utils import get_field_list
from app.support import Country, Site, Drink, Item, Region, Subregion, Parcel


class ParcelRepository(Repository):
    model = Parcel

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.parcel_id == id
        )


class SiteRepository(Repository):
    model = Site

    @classmethod
    def item_exists(cls, id: int):
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.site_id == id
        )

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Site).options(
            selectinload(Site.subregion).selectinload(Subregion.region).selectinload(Region.country)
        )

@classmethod
    def get_short_query(cls, model: Site, field1: tuple = ('id', 'name', 'country_id', 'region_id', 'subregion_id')):
        """
            Возвращает список модели только с нужными полями остальные None
            - использовать для list_view и вообще где только можно.
            для моделей с зависимостями - переопределить
        """

        fields = get_field_list(model, starts=field1)
        subcat = get_field_list(Country, starts=field1)
        tier3 = get_field_list(Region, starts=field1)
        tier3 = get_field_list(Subregion, starts = field1)
        return select(model).options(
            joinedload(model.subregion).joinedload(Subregion.region).load_only(*tier3)
            .joinedload(Region.country).load_only(*subcat),
            load_only(*fields)
        )