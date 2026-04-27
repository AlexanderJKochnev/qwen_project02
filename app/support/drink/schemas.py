# app/support/drink/schemas.py
from datetime import datetime
from typing import List, Optional

from pydantic import Field, field_serializer

from app.core.schemas.base import (BaseModel, CreateNoNameSchema, CreateResponse, ReadNoNameSchema, UpdateNoNameSchema)
from app.support.drink.drink_food_schema import DrinkFoodRelation
from app.support.drink.drink_varietal_schema import (DrinkVarietalId, DrinkVarietalRelation, DrinkVarietalRelationFlat)
from app.support.food.schemas import FoodCreateRelation
from app.support.parcel.schemas import SiteCreateRelation, SiteRead
from app.support.producer.schemas import ProducerCreateRelation, ProducerRead
from app.support.source.schemas import SourceCreateRelation, SourceRead
from app.support.subcategory.schemas import SubcategoryCreateRelation, SubcategoryRead, SubcategoryReadRelation
# from app.support.subregion.schemas import SubregionCreateRelation, SubregionRead, SubregionReadRelation
from app.support.sweetness.schemas import SweetnessCreateRelation, SweetnessRead, SweetnessReadRelation
from app.support.varietal.schemas import VarietalRead
from app.support.vintage.schemas import (ClassificationCreateRelation, ClassificationRead, DesignationCreateRelation,
                                         DesignationRead, VintageConfigCreateRelation, VintageConfigRead)


class LangMixin:
    # title: Optional[str] = None
    title_ru: Optional[str] = None
    title_fr: Optional[str] = None
    title_es: Optional[str] = None
    title_it: Optional[str] = None
    title_de: Optional[str] = None
    title_zh: Optional[str] = None

    subtitle: Optional[str] = None
    subtitle_ru: Optional[str] = None
    subtitle_fr: Optional[str] = None
    subtitle_es: Optional[str] = None
    subtitle_it: Optional[str] = None
    subtitle_de: Optional[str] = None
    subtitle_zh: Optional[str] = None

    description: Optional[str] = None
    description_ru: Optional[str] = None
    description_fr: Optional[str] = None
    description_es: Optional[str] = None
    description_it: Optional[str] = None
    description_de: Optional[str] = None
    description_zh: Optional[str] = None

    recommendation: Optional[str] = None
    recommendation_ru: Optional[str] = None
    recommendation_fr: Optional[str] = None
    recommendation_es: Optional[str] = None
    recommendation_it: Optional[str] = None
    recommendation_de: Optional[str] = None
    recommendation_zh: Optional[str] = None

    madeof: Optional[str] = None
    madeof_ru: Optional[str] = None
    madeof_fr: Optional[str] = None
    madeof_es: Optional[str] = None
    madeof_it: Optional[str] = None
    madeof_de: Optional[str] = None
    madeof_zh: Optional[str] = None


class LangMixinExclude:
    # для вычисляемых столбцов
    title: Optional[str] = Field(exclude=True)
    title_ru: Optional[str] = Field(exclude=True)
    title_fr: Optional[str] = Field(exclude=True)
    title_es: Optional[str] = Field(exclude=True)
    title_it: Optional[str] = Field(exclude=True)
    title_de: Optional[str] = Field(exclude=True)
    title_zh: Optional[str] = Field(exclude=True)

    subtitle: Optional[str] = Field(exclude=True)
    subtitle_ru: Optional[str] = Field(exclude=True)
    subtitle_fr: Optional[str] = Field(exclude=True)
    subtitle_es: Optional[str] = Field(exclude=True)
    subtitle_it: Optional[str] = Field(exclude=True)
    subtitle_de: Optional[str] = Field(exclude=True)
    subtitle_zh: Optional[str] = Field(exclude=True)

    description: Optional[str] = Field(exclude=True)
    description_ru: Optional[str] = Field(exclude=True)
    description_fr: Optional[str] = Field(exclude=True)
    description_es: Optional[str] = Field(exclude=True)
    description_it: Optional[str] = Field(exclude=True)
    description_de: Optional[str] = Field(exclude=True)
    description_zh: Optional[str] = Field(exclude=True)

    recommendation: Optional[str] = Field(exclude=True)
    recommendation_ru: Optional[str] = Field(exclude=True)
    recommendation_fr: Optional[str] = Field(exclude=True)
    recommendation_es: Optional[str] = Field(exclude=True)
    recommendation_it: Optional[str] = Field(exclude=True)
    recommendation_de: Optional[str] = Field(exclude=True)
    recommendation_zh: Optional[str] = Field(exclude=True)

    madeof: Optional[str] = Field(exclude=True)
    madeof_ru: Optional[str] = Field(exclude=True)
    madeof_fr: Optional[str] = Field(exclude=True)
    madeof_es: Optional[str] = Field(exclude=True)
    madeof_it: Optional[str] = Field(exclude=True)
    madeof_de: Optional[str] = Field(exclude=True)
    madeof_zh: Optional[str] = Field(exclude=True)


class NewUpdSchema:
    lwin: Optional[str] = None
    display_name: Optional[str] = None
    anno: Optional[str] = None
    producer_id: Optional[int] = None
    source_id: Optional[int] = None
    vintageconfig_id: Optional[int] = None
    classification_id: Optional[int] = None
    designation_id: Optional[int] = None
    site_id: Optional[int] = None
    first_vintage: Optional[str] = Field(default=None)
    last_vintage: Optional[str] = Field(default=None)


class NewCreateSchema:
    lwin: Optional[str] = None
    display_name: Optional[str] = None
    anno: Optional[str] = None
    producer_id: Optional[int] = None
    source_id: int
    vintageconfig_id: Optional[int] = None
    classification_id: Optional[int] = None
    designation_id: Optional[int] = None
    site_id: Optional[int] = None
    first_vintage: Optional[str] = Field(default=None)
    last_vintage: Optional[str] = Field(default=None)


class NewReadSchema:
    lwin: Optional[str] = None
    display_name: Optional[str] = None
    anno: Optional[str] = None
    producer: Optional[ProducerRead] = None
    source: SourceRead
    classification: Optional[ClassificationRead]
    vintageconfig: Optional[VintageConfigRead]
    designation: Optional[DesignationRead]
    site: SiteRead
    first_vintage: Optional[str] = Field(default=None)
    last_vintage: Optional[str] = Field(default=None)


class NewCreateRelationsSchema:
    producer: Optional[ProducerCreateRelation] = None
    source: SourceCreateRelation
    classification: Optional[ClassificationCreateRelation]
    vintageconfig: Optional[VintageConfigCreateRelation]
    designation: Optional[DesignationCreateRelation]
    site: SiteCreateRelation
    first_vintage: Optional[int] = Field(default=None, ge=1000, le=3000)
    last_vintage: Optional[int] = Field(default=None, ge=1000, le=3000)


class CustomUpdSchema(LangMixin, NewUpdSchema):
    title: Optional[str] = None
    subcategory_id: Optional[int] = None
    sweetness_id: Optional[int] = None
    # subregion_id: Optional[int] = None
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    # foods: Optional[List[FoodId]] = None
    varietals: Optional[List[DrinkVarietalId]] = None


class CustomCreateSchema(LangMixin, NewCreateSchema):
    title: str
    subcategory_id: int
    sweetness_id: Optional[int] = None
    # subregion_id: int
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None


class DrinkFoodVarietalSchema:
    foods: Optional[List[FoodCreateRelation]] = None
    varietals: Optional[List[DrinkVarietalRelation]] = None
    pass


class CustomCreateDrinkItem(LangMixin, NewCreateSchema):
    """
         для  схемы ItemDrinkCreate
    """
    title: str
    subcategory_id: Optional[int] = Field(exclude=True)
    sweetness_id: Optional[int] = Field(exclude=True)
    # subregion_id: Optional[int] = Field(exclude=True)
    alc: Optional[float] = Field(exclude=True)
    sugar: Optional[float] = Field(exclude=True)
    age: Optional[str] = Field(exclude=True)
    # foods: Optional[List[FoodId]] = None
    # varietals: Optional[List[DrinkVarietalId]] = None


class CustomCreateRelation(LangMixin, NewCreateRelationsSchema):
    title: str
    subcategory: SubcategoryCreateRelation
    sweetness: Optional[SweetnessCreateRelation] = None
    # subregion: SubregionCreateRelation
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    # foods: Optional[List[FoodCreateRelation]] = None
    # varietals: Optional[List[DrinkVarietalRelation]] = None


class CustomReadRelation(LangMixin, NewReadSchema):
    title: str
    subcategory: SubcategoryReadRelation
    sweetness: Optional[SweetnessReadRelation] = None
    # subregion: SubregionReadRelation
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    varietal_associations: Optional[List[DrinkVarietalRelation]] = Field(exclude=True)
    # foods: Optional[list] = []
    food_associations: Optional[List[DrinkFoodRelation]] = Field(exclude=True)

    @property
    def varietals(self):
        return [{"varietal": assoc.varietal, "percentage": assoc.percentage}
                for assoc in self.varietal_associations]

    @property
    def foods(self):
        return [assoc.model_dump() for assoc in self.food_associations]


class CustomReadSchema(LangMixin, NewReadSchema):
    title: Optional[str] = None
    subcategory: SubcategoryRead
    sweetness: Optional[SweetnessRead] = None
    # subregion: Optional[SubregionRead] = None
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    # foods: List[FoodRead]
    varietals: List[VarietalRead]
    varietal_associations: Optional[List[DrinkVarietalRelationFlat]] = []
    food_associations: List[DrinkFoodRelation] = []
    updated_at: Optional[datetime] = None

    @field_serializer('alc', when_used='unless-none')
    def serialize_alc(self, value: Optional[float]) -> Optional[str]:
        if value is None:
            return None
        return f"{int(round(value))}"

    @field_serializer('sugar', when_used='unless-none')
    def serialize_sugar(self, value: Optional[float]) -> Optional[str]:
        if value is None:
            return None
        return f"{int(round(value))}"


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
        drink
        костыль: # app.support.drink.service.py разобраться должен полдойти просто DrinkCreate
    """
    pass


class DrinkCreate(CreateNoNameSchema, CustomCreateSchema):
    # foods: Optional[List[FoodId]] = None
    # varietals: Optional[List[DrinkVarietalId]] = None
    pass


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
