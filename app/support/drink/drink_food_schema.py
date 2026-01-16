# app/support/drink/drink_food_schema.py
#
from typing import List
from pydantic import Field
from app.core.schemas.base import BaseModel, ConfigDict
from app.core.schemas.api_mixin import LangMixin
from app.support.food.schemas import FoodRead, FoodReadRelation


class DrinkFoodRelation(BaseModel):
    food: FoodReadRelation


class DrinkFoodRelationApi(LangMixin):
    model_config = ConfigDict(from_attributes=True,
                              arbitrary_types_allowed=True,
                              extra='allow',
                              populate_by_name=True,
                              exclude_none=True)
    food: FoodRead = Field(exclude=True)

    def __get_lang__(self, lang: str = '_ru', ) -> str:
        schema, field_name = self.food, 'name'
        if schema:
            prefix = getattr(schema, f'{field_name}{lang}') or getattr(schema, f'{field_name}')
            return prefix
        return None


class DrinkFoodLinkCreate(BaseModel):
    drink_id: int
    food_ids: List[int]  # полный список ID для связи


class DrinkFoodLinkUpdate(BaseModel):
    food_ids: List[int]
