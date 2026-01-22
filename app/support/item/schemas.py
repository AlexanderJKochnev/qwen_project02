# app/support/item/schemas.py

from typing import Optional, List, Tuple
from datetime import datetime
from pydantic import Field
from app.core.schemas.image_mixin import ImageUrlMixin
from app.core.schemas.base import BaseModel, CreateResponse
from app.support.drink.schemas import (DrinkCreateRelation,
                                       DrinkReadRelation, DrinkCreate, LangMixin)


"""
class CustomReadFlatSchema:
    id: int
    drink: DrinkReadFlat = Field(exclude=True)
    updated_at: datetime = Field(exclude=True)
    vol: Optional[float] = None
    # price: Optional[float] = None
    # count: Optional[int] = 0

    @computed_field
    @property
    def changed_at(self) -> datetime:
        return getattr(self.drink, "updated_at") or self.updated_at

    @computed_field
    @property
    def country(self) -> str:
        if hasattr(self.drink, 'subregion'):
            if hasattr(self.drink.subregion, 'region'):
                if hasattr(self.drink.subregion.region, 'country'):
                    if hasattr(self.drink.subregion.region.country, 'name'):
                        return camel_to_enum(self.drink.subregion.region.country.name)
        return None

    @computed_field
    @property
    def category(self) -> str:
        if hasattr(self.drink, 'subcategory'):
            if hasattr(self.drink.subcategory, 'category'):
                if hasattr(self.drink.subcategory.category, 'name'):
                    if self.drink.subcategory.category.name == 'Wine':
                        return camel_to_enum(self.drink.subcategory.name)
                    else:
                        return camel_to_enum(self.drink.subcategory.category.name)
        return None

    def _lang_(self, lang: str = 'en') -> Dict[str, Any]:
        return getattr(self.drink, lang)

    @computed_field
    @property
    def en(self) -> Dict[str, Any]:
        return self._lang_('en')

    @computed_field
    @property
    def ru(self) -> Dict[str, Any]:
        return self._lang_('ru')

    @computed_field
    @property
    def fr(self) -> Dict[str, Any]:
        return self._lang_('fr')
"""


class CustomCreateSchema:
    drink_id: int
    vol: Optional[float] = None
    price: Optional[float] = None
    count: Optional[int] = 0
    image_path: Optional[str] = None
    image_id: Optional[str] = None


class CustomReadSchema(CustomCreateSchema):
    id: int


class CustomReadRelation:
    id: int
    drink: DrinkReadRelation
    vol: Optional[float] = None
    price: Optional[float] = None
    count: Optional[int] = 0
    image_path: Optional[str] = None
    image_id: Optional[str] = None


class CustomCreateRelation:
    drink: DrinkCreateRelation
    vol: Optional[float] = None
    price: Optional[float] = None
    count: Optional[int] = 0
    image_path: Optional[str] = None
    image_id: Optional[str] = None


class DirectUploadSchema(BaseModel):
    total_input: int
    count_of_added_records: int
    error: Optional[list] = None
    error_nmbr: Optional[int] = None


class FileUpload(BaseModel):
    filename: Optional[str] = 'data.json'


class CustomUpdSchema:
    drink_id: Optional[int] = None
    vol: Optional[float] = None
    price: Optional[float] = None
    count: Optional[int] = 0
    image_path: Optional[str] = None
    image_id: Optional[str] = None


class ItemCreate(BaseModel, CustomCreateSchema, ImageUrlMixin):
    pass


class ItemCreatePreact(DrinkCreate, ImageUrlMixin):
    vol: Optional[float] = None
    price: Optional[float] = None
    count: Optional[int] = 0


class ItemReadPreactForUpdate(ItemCreatePreact):
    """ схема для получения данных для обновления в Preact"""
    id: int
    drink_id: int


class ItemUpdate(BaseModel, CustomUpdSchema, ImageUrlMixin):
    pass


class ItemUpdatePreact(ItemCreatePreact):
    """ схема для обновления данных для Preact """
    drink_action: str  # 'update' or 'create'
    drink_id: Optional[int] = None
    id: Optional[int] = None


class ItemCreateResponseSchema(CreateResponse, ItemCreate):
    pass


class ItemCreateRelation(BaseModel, CustomCreateRelation, ImageUrlMixin):
    pass


# -------------------preact schemas-----------------------

"""
class DrinkPreactDetailView:
    #  похоже нигде не используется
    id: int
    drink: DrinkReadApi


class DrinkPreactListView:
    id: int
    drink: int
    vol: Optional[float] = None


class DrinkPreactUpdate:
    id: int


class DrinkPreactCreate:
    title: str
    title_ru: Optional[str]
    title_fr: Optional[str]
"""


class ItemListView(BaseModel):
    # поля не зависят от параметра lang в роуте
    id: int  # Item.id
    vol: Optional[float] = None  # Item.vol
    image_id: Optional[str] = None  # Item.image_id

    title: str  # Item.drinks.title or Item.drinks.title_ru or Item.drinks.title_fr зависит от параметра lang в роуте
    category: str  # Item.drink.subcategoory.category.name + Item.drink.subcategoory.name
    country: str  # Country.name or country.name_ru, or country.name_fr зависит от параметра lang в роуте


class ItemDetailNonLocalized(BaseModel):
    # поля не зависят от параметра lang в роуте
    id: int  # Item.id
    vol: Optional[float] = None  # Item.vol
    alc: Optional[str] = None
    age: Optional[str] = None
    image_id: Optional[str] = None  # Item.image_id


class ItemDetailForeignLocalized(BaseModel):
    category: Optional[str] = None
    subcategory: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    subregion: Optional[str] = None
    sweetness: Optional[str] = None


class ItemDetailLocalized(BaseModel):
    # поля зависящие от параметра lang в роуте
    title: str  # Item.drink.title or Item.drinks.title_ru or Item.drinks.title_fr
    subtitle: Optional[str] = None
    recommendation: Optional[str] = None   # Drink.recommendation (_ru, _fr)
    madeof: Optional[str] = None  # Drink.madeof (_ru, _fr)
    description: Optional[str] = None  # Drink.description (_ru, _fr)


class ItemDetailManyToManyLocalized(BaseModel):
    pairing: Optional[List[str]] = None  # From Drink.food_associations
    varietal: Optional[List[str]] = None  # From Drink.varietal_associations


class ItemDetailView(ItemDetailManyToManyLocalized, ItemDetailForeignLocalized,
                     ItemDetailNonLocalized,
                     ItemDetailLocalized,
                     ):

    model_config = {'populate_by_name': True, 'str_strip_whitespace': True}

    def model_dump(self, exclude_none=True, **kwargs):
        # Override model_dump to exclude None and empty values
        data = super().model_dump(exclude_none=True, **kwargs)
        # Remove empty strings and empty lists
        cleaned_data = {}
        for key, value in data.items():
            if value is not None and value != '' and value != []:
                cleaned_data[key] = value
        return cleaned_data


class ItemDrinkPreactSchema(LangMixin, ImageUrlMixin, BaseModel):
    # перечисленные ниже поля из модели Drink
    title: str
    subcategory_id: int
    sweetness_id: Optional[int] = None
    subregion_id: int
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    # Drink - DrinkVarietal
    varietals: Optional[List[Tuple[int, float]]] = None
    # Drink - DrinkFood
    foods: Optional[List[int]] = None
    # Item - Drink
    vol: Optional[float] = None
    price: Optional[float] = None
    image_id: Optional[str] = None
    image_path: Optional[str] = None


class ItemApiLangNonLocalized(BaseModel):
    alc: Optional[str] = None  # "12.5%"
    vol: Optional[str] = None  # "0.75 l"


class ItemApiLangLocalized(ItemDetailLocalized):
    region: Optional[str] = None  # Region. Subregion


class ItemApiLang(ItemDetailManyToManyLocalized, ItemDetailLocalized, ItemApiLangNonLocalized):
    pass


class ItemApiRoot(BaseModel):
    """
      fields for root levele of api_items
      SHALL be equal .env API_ROOT_FIELDS
    """
    id: int
    country: str
    category: str
    image_id: Optional[str] = None
    image_path: Optional[str] = None
    changed_at: datetime = Field(exclude=True)


class ItemApi(ItemApiRoot):
    en: ItemApiLang
    ru: ItemApiLang
    fr: ItemApiLang
    es: ItemApiLang
    it: ItemApiLang
    de: ItemApiLang
    cn: ItemApiLang


class ItemRead(BaseModel, CustomReadSchema, ImageUrlMixin):
    pass


class ItemReadRelation(BaseModel, CustomReadRelation, ImageUrlMixin):
    pass


class ItemReadPreact(ItemRead):
    """
        {
          "title_ru": "string",
          "title_fr": "string",
          "subtitle": "string",
          "subtitle_ru": "string",
          "subtitle_fr": "string",
          "description": "string",
          "description_ru": "string",
          "description_fr": "string",
          "recommendation": "string",
          "recommendation_ru": "string",
          "recommendation_fr": "string",
          "madeof": "string",
          "madeof_ru": "string",
          "madeof_fr": "string",
          "title": "string",
          "subcategory_id": 0,
          "sweetness_id": 0,
          "subregion_id": 0,
          "alc": 0,
          "sugar": 0,
          "age": "string",
          "image_id": "string",
          "image_path": "string",
          "foods": [
            {
              "id": 0
            }
          ],
          "varietals": [
            {
              "id": 0,
              "percentage": 0
            }
          ],
          "vol": 0,
          "price": 0,
          "count": 0,
          "id": 0,
          "drink_id": 0
        }
    """
    pass
