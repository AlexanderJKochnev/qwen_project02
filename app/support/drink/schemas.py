# app/support/drink/schemas.py
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import field_serializer, Field, computed_field
from app.core.utils.common_utils import camel_to_enum
from app.core.schemas.base import (BaseModel, CreateNoNameSchema, CreateResponse, PkSchema,
                                   ReadNoNameSchema, UpdateNoNameSchema, ReadApiSchema)
from app.support.drink.drink_varietal_schema import (DrinkVarietalRelation, DrinkVarietalRelationFlat,
                                                     DrinkVarietalRelationApi, DrinkVarietalId)
from app.support.drink.drink_food_schema import DrinkFoodRelationApi, DrinkFoodRelation
from app.support.food.schemas import FoodCreateRelation, FoodRead, FoodId
from app.support.subcategory.schemas import SubcategoryCreateRelation, SubcategoryRead, SubcategoryReadApiSchema
from app.support.subregion.schemas import SubregionCreateRelation, SubregionRead, SubregionReadApiSchema
from app.support.sweetness.schemas import SweetnessCreateRelation, SweetnessRead
from app.support.varietal.schemas import VarietalRead
from app.core.config.project_config import settings


class LangMixin:
    title: Optional[str] = None
    title_ru: Optional[str] = None
    title_fr: Optional[str] = None

    subtitle: Optional[str] = None
    subtitle_ru: Optional[str] = None
    subtitle_fr: Optional[str] = None

    description: Optional[str] = None
    description_ru: Optional[str] = None
    description_fr: Optional[str] = None

    recommendation: Optional[str] = None
    recommendation_ru: Optional[str] = None
    recommendation_fr: Optional[str] = None

    madeof: Optional[str] = None
    madeof_ru: Optional[str] = None
    madeof_fr: Optional[str] = None


class LangMixinExclude:
    """
        для вычисляемых столбцов
    """
    title: Optional[str] = Field(exclude=True)
    title_ru: Optional[str] = Field(exclude=True)
    title_fr: Optional[str] = Field(exclude=True)

    subtitle: Optional[str] = Field(exclude=True)
    subtitle_ru: Optional[str] = Field(exclude=True)
    subtitle_fr: Optional[str] = Field(exclude=True)

    description: Optional[str] = Field(exclude=True)
    description_ru: Optional[str] = Field(exclude=True)
    description_fr: Optional[str] = Field(exclude=True)

    recommendation: Optional[str] = Field(exclude=True)
    recommendation_ru: Optional[str] = Field(exclude=True)
    recommendation_fr: Optional[str] = Field(exclude=True)

    madeof: Optional[str] = Field(exclude=True)
    madeof_ru: Optional[str] = Field(exclude=True)
    madeof_fr: Optional[str] = Field(exclude=True)


class CustomUpdSchema(LangMixin):
    subcategory_id: Optional[int] = None
    sweetness_id: Optional[int] = None
    subregion_id: Optional[int] = None
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    foods: Optional[List[FoodId]] = None
    varietals: Optional[List[DrinkVarietalId]] = None


class CustomCreateSchema(LangMixin):
    title: str
    subcategory_id: int
    sweetness_id: Optional[int] = None
    subregion_id: int
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None


class DrinkFoodVarietalSchema:
    foods: Optional[List[FoodCreateRelation]] = None
    varietals: Optional[List[DrinkVarietalRelation]] = None


class CustomCreateDrinkItem(LangMixin):
    """
         для  схемы ItemDrinkCreate
    """
    subcategory_id: Optional[int] = Field(exclude=True)
    sweetness_id: Optional[int] = Field(exclude=True)
    subregion_id: Optional[int] = Field(exclude=True)
    alc: Optional[float] = Field(exclude=True)
    sugar: Optional[float] = Field(exclude=True)
    age: Optional[str] = Field(exclude=True)
    foods: Optional[List[FoodId]] = None
    varietals: Optional[List[DrinkVarietalId]] = None


class CustomCreateRelation(LangMixin):
    title: str
    subcategory: SubcategoryCreateRelation
    sweetness: Optional[SweetnessCreateRelation] = None
    subregion: SubregionCreateRelation
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    foods: Optional[List[FoodCreateRelation]] = None
    varietals: Optional[List[DrinkVarietalRelation]] = None


class CustomReadRelation(LangMixin):
    title: str
    subcategory: SubcategoryCreateRelation
    sweetness: Optional[SweetnessCreateRelation] = None
    subregion: SubregionCreateRelation
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    varietal_associations: Optional[List[DrinkVarietalRelation]] = Field(exclude=True)
    food_associations: Optional[List[DrinkFoodRelation]] = Field(exclude=True)

    @property
    def varietals(self):
        return [{"varietal": assoc.varietal, "percentage": assoc.percentage}
                for assoc in self.varietal_associations]

    @property
    def foods(self):
        return [assoc.model_dump() for assoc in self.food_associations]


class CustomReadSchema(LangMixin):
    subcategory: SubcategoryRead
    sweetness: Optional[SweetnessRead] = None
    subregion: Optional[SubregionRead] = None
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    foods: List[FoodRead]
    varietals: List[VarietalRead]
    varietal_associations: Optional[List[DrinkVarietalRelationFlat]]
    food_associations: List[DrinkFoodRelation] = []
    updated_at: Optional[datetime] = None

    @field_serializer('alc', when_used='unless-none')
    def serialize_alc(self, value: Optional[float]) -> Optional[str]:
        if value is None:
            return None
        return f"{int(round(value))}%"

    @field_serializer('sugar', when_used='unless-none')
    def serialize_sugar(self, value: Optional[float]) -> Optional[str]:
        if value is None:
            return None
        return f"{int(round(value))}%"


class DrinkRead(ReadNoNameSchema, CustomReadSchema):
    """
    model_config = ConfigDict(from_attributes=True,
                              arbitrary_types_allowed=True,
                              extra='allow',
                              populate_by_name=True,
                              exclude_none=True)
    """
    pass


class DrinkReadRelation(ReadNoNameSchema, CustomReadSchema):
    pass


class DrinkCreate1(CreateNoNameSchema, CustomCreateSchema, DrinkFoodVarietalSchema):
    """
        костыль: # app.support.drink.service.py разобраться должен полдойти просто DrinkCreate
    """
    pass


class DrinkCreate(CreateNoNameSchema, CustomCreateSchema):
    foods: Optional[List[FoodId]] = None
    varietals: Optional[List[DrinkVarietalId]] = None


class DrinkCreateRelation(CreateNoNameSchema, CustomCreateRelation):
    pass


class DrinkCreateItems(CreateNoNameSchema, CustomCreateDrinkItem):
    pass


class DrinkUpdate(CustomUpdSchema, UpdateNoNameSchema):
    pass


class DrinkCreateResponseSchema(DrinkCreate, CreateResponse):
    pass


class DrinkFoodLinkCreate(BaseModel):
    drink_id: int
    food_ids: List[int]  # полный список ID для связи


class DrinkFoodLinkUpdate(BaseModel):
    food_ids: List[int]


class DrinkVarietalLinkCreate(BaseModel):
    drink: DrinkRead


class CustomReadApiSchema(LangMixinExclude):
    subcategory: SubcategoryReadApiSchema = Field(exclude=True)
    sweetness: Optional[ReadApiSchema] = Field(exclude=True)
    subregion: Optional[SubregionReadApiSchema] = Field(exclude=True)
    alc: Optional[float] = Field(exclude=True)
    sugar: Optional[float] = Field(exclude=True)
    age: Optional[str] = Field(exclude=True)
    foods: Optional[List[FoodRead]] = Field(exclude=True)
    food_associations: Optional[List[DrinkFoodRelationApi]] = Field(exclude=True)
    varietal_associations: Optional[List[DrinkVarietalRelationApi]] = Field(exclude=True)
    updated_at: Optional[datetime] = None

    def __get_field_value__(self, field_name: str, lang_suffix: str) -> Any:
        """
            Получить значение поля с учетом языкового суффикса
            Если нет значения на языке - берется значение из поля по молчанию (english)
        """
        lang_field = f"{field_name}{lang_suffix}"
        if hasattr(self, lang_field):
            value = getattr(self, lang_field)
            if value is not None:
                return value

        # Если нет поля с суффиксом, пробуем базовое поле
        if hasattr(self, field_name):
            return getattr(self, field_name)
        return None

    def __get_nested_field__(self, obj, field_path: str, lang_suffix: str) -> Any:
        """Получить значение из вложенного объекта"""
        if obj is None:
            return None

        fields = field_path.split('.')
        current_obj = obj

        for field in fields:
            if hasattr(current_obj, field):
                current_obj = getattr(current_obj, field)
            else:
                return None

        # Для вложенных объектов рекурсивно ищем языковые версии
        # print(f'{current_obj=} {type(current_obj)} {lang_suffix=}, ', hasattr(current_obj, f"name{lang_suffix}"))
        if hasattr(current_obj, f"name{lang_suffix}"):
            return getattr(current_obj, f"name{lang_suffix}")
        elif hasattr(current_obj, "name"):
            return current_obj.name

        return str(current_obj) if current_obj else None

    def __get_association_names__(self, associations: List, lang_suffix: str) -> str:
        """Получить строку названий ассоциаций"""
        if not associations:
            return ""

        names = []
        for assoc in associations:
            if hasattr(assoc, f"name{lang_suffix}"):
                name = getattr(assoc, f"name{lang_suffix}")
            elif hasattr(assoc, "name"):
                name = assoc.name
            else:
                continue
            if name:
                names.append(name)

        return ", ".join(names) if names else ""

    def __parser__(self, lang_suffix: str) -> Dict[str, Any]:
        """Парсер для преобразования полей в словарь по языкам"""

        # Динамически создаем маппинг суффиксов на названия языков
        lang_map = {"": settings.DEFAULT_LANG}
        for lang in settings.LANGUAGES:
            if lang != settings.DEFAULT_LANG:
                lang_map[f"_{lang}"] = lang
        current_lang = lang_map.get(lang_suffix, settings.DEFAULT_LANG)

        result = {}

        # Категория и подкатегория
        if self.subcategory:
            # ЗДЕСЬ РАЗОБРАТЬСЯ С WINE RED -> RED
            # result["category"] = self.__get_nested_field__(self.subcategory, "category.name", lang_suffix)
            # result["subcategory"] = self.__get_nested_field__(self.subcategory, "name", lang_suffix)
            category_name = self.__get_nested_field__(self.subcategory, "category.name", lang_suffix)
            subcategory_name = self.__get_nested_field__(self.subcategory, "name", lang_suffix)
            if category_name and subcategory_name:
                # result['category'] = f"{category_name} {subcategory_name}"
                result['category'] = f"{subcategory_name}"
            else:
                result['category'] = f"{category_name}"

        # Сладость
        if self.sweetness:
            result["sweetness"] = self.__get_nested_field__(self.sweetness, "name", lang_suffix)

        # Регион и страна
        if self.subregion:
            region_name = self.__get_nested_field__(self.subregion, "name", lang_suffix)
            country_name = self.__get_nested_field__(self.subregion, "region.country.name", lang_suffix)

            if region_name and country_name:
                result["region"] = f"{region_name}, {country_name}"
                result["country"] = country_name
            elif region_name:
                result["region"] = region_name
                result["country"] = self.__get_nested_field__(self.subregion, "region.country.name", lang_suffix)

        # Рекомендации
        result["recommendation"] = self.__get_field_value__("recommendation", lang_suffix)

        # Description
        result["description"] = self.__get_field_value__("description", lang_suffix)

        # Состав
        result["madeof"] = self.__get_field_value__("madeof", lang_suffix)

        # Title
        result["title"] = self.__get_field_value__("title", lang_suffix)

        # Subitle
        result["subtitle"] = self.__get_field_value__("subtitle", lang_suffix)

        # Пайринг (еда)
        result["pairing"] = self.__get_association_names__(self.food_associations, lang_suffix)

        # Сорта винограда
        result["varietals"] = self.__get_association_names__(self.varietal_associations, lang_suffix)

        # Общие поля (одинаковые для всех языков)
        if self.alc is not None:
            result["alc"] = f"{self.alc}%" if current_lang == settings.DEFAULT_LANG else f"{self.alc}%"

        if self.sugar is not None:
            result["sugar"] = f"{self.sugar}%" if current_lang == settings.DEFAULT_LANG else f"{self.sugar}%"

        result["age"] = self.age

        # Убираем None значения
        return {k: v for k, v in result.items() if v is not None}

    @computed_field
    @property
    def en(self) -> Dict[str, Any]:
        """Default language version"""
        return self.__parser__("")

    @computed_field
    @property
    def ru(self) -> Dict[str, Any]:
        """Russian language version"""
        if 'ru' in settings.LANGUAGES and settings.DEFAULT_LANG != 'ru':
            return self.__parser__("_ru")
        return self.__parser__("")

    @computed_field
    @property
    def fr(self) -> Dict[str, Any]:
        """French language version"""
        if 'fr' in settings.LANGUAGES and settings.DEFAULT_LANG != 'fr':
            return self.__parser__("_fr")
        return self.__parser__("")


class DrinkReadApi(PkSchema, CustomReadApiSchema):
    pass


class CustomReadFlatSchema(LangMixinExclude):
    subcategory: SubcategoryReadApiSchema = Field(exclude=True)
    sweetness: Optional[ReadApiSchema] = Field(exclude=True)
    subregion: Optional[SubregionReadApiSchema] = Field(exclude=True)
    alc: Optional[float] = Field(exclude=True)
    sugar: Optional[float] = Field(exclude=True)
    age: Optional[str] = Field(exclude=True)
    foods: Optional[List[FoodRead]] = Field(exclude=True)
    food_associations: Optional[List[DrinkFoodRelationApi]] = Field(exclude=True)
    varietal_associations: Optional[List[DrinkVarietalRelationApi]] = Field(exclude=True)
    updated_at: Optional[datetime] = None

    def _get_base_field_names(self) -> set[str]:
        """
        Автоматически определяет базовые языковые поля по наличию полей с суффиксом '_ru'.
        Например: если есть 'title_ru' → базовое поле 'title'.
        """
        field_names = self.model_fields.keys()
        base_fields = set()
        for name in field_names:
            if name.endswith('_ru'):
                base_name = name[:-3]  # убираем '_ru'
                base_fields.add(base_name)
        return base_fields

    def __get_field_value__(self, field_name: str, lang_suffix: str) -> Any:
        """
            Получить значение поля с учетом языкового суффикса
            Если нет значения на языке - берется значение из поля по молчанию (english)
        """
        lang_field = f"{field_name}{lang_suffix}"
        if hasattr(self, lang_field):
            value = getattr(self, lang_field)
            if value is not None:
                return value

        # Если нет поля с суффиксом, пробуем базовое поле
        if hasattr(self, field_name):
            return getattr(self, field_name)
        return None

    @computed_field
    @property
    def country(self) -> str:
        if hasattr(self.subregion, 'region'):
            if hasattr(self.subregion.region, 'country'):
                if hasattr(self.subregion.region.country, 'name'):
                    return camel_to_enum(self.subregion.region.country.name)
        return None

    @computed_field
    @property
    def category(self) -> str:
        if hasattr(self.subcategory, 'category'):
            if hasattr(self.subcategory.category, 'name'):
                if self.subcategory.category.name == 'Wine':
                    return camel_to_enum(self.subcategory.name)
                else:
                    return camel_to_enum(self.subcategory.category.name)
        return None

    def _lang_(self, lang_suffix: str = '') -> Dict[str, Any]:
        result: dict = {}
        # добавляем поля из языковой модели
        for field in self._get_base_field_names():
            fname = f'{field}{lang_suffix}'
            res = getattr(self, fname, None) or getattr(self, field, None)
            if res:
                result[field] = res
        if self.alc:
            result['alc'] = f'{self.alc}%'
        if self.sugar:
            result['sugar'] = f'{self.sugar}%'
        if self.age:
            result['age'] = f'{self.age}%'
        many = ((self.food_associations, 'pairing'),
                (self.varietal_associations, 'varietal'))
        for key, v1 in many:
            if key:
                tmp = [getattr(v, f'name{lang_suffix}') or getattr(v, 'name') for v in key]
                if tmp:
                    # если нужна строка - use tmp_str instead of tmp
                    # tmp_str = ', '.join(tmp)
                    result[v1] = tmp
        return result

    @computed_field
    @property
    def en(self) -> Dict[str, Any]:
        return self._lang_('')

    @computed_field
    @property
    def ru(self) -> Dict[str, Any]:
        if 'ru' in settings.LANGUAGES and settings.DEFAULT_LANG != 'ru':
            return self._lang_('_ru')
        return self._lang_('')

    @computed_field
    @property
    def fr(self) -> Dict[str, Any]:
        if 'fr' in settings.LANGUAGES and settings.DEFAULT_LANG != 'fr':
            return self._lang_('_fr')
        return self._lang_('')


class DrinkReadFlat(BaseModel, CustomReadFlatSchema):
    id: int
