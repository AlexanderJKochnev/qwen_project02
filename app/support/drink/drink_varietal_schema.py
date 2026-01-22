# app/support/drink/drink_varietal_schema.py
from pydantic import Field
from typing import List, Optional
from app.core.schemas.base import BaseModel, ConfigDict
# from app.core.schemas.api_mixin import LangMixin
from app.support.varietal.schemas import VarietalCreateRelation


class DrinkVarietalId(BaseModel):
    id: int     # varietal id
    percentage: Optional[float] = None


class DrinkVarietalRelation(BaseModel):
    model_config = ConfigDict(from_attributes=True,
                              arbitrary_types_allowed=True,
                              extra='allow',
                              populate_by_name=True,
                              exclude_none=True)
    varietal: VarietalCreateRelation
    percentage: Optional[float] = None


class DrinkVarietalRelationFlat(BaseModel):
    model_config = ConfigDict(from_attributes=True,
                              arbitrary_types_allowed=True,
                              extra='allow',
                              populate_by_name=True,
                              exclude_none=True)
    varietal: VarietalCreateRelation
    percentage: Optional[float]


"""
class DrinkVarietalRelationApi(LangMixin):
    model_config = ConfigDict(from_attributes=True,
                              arbitrary_types_allowed=True,
                              extra='allow',
                              populate_by_name=True,
                              exclude_none=True)
    varietal: VarietalCreateRelation = Field(exclude=True)
    percentage: Optional[float] = Field(default=None, exclude=True)

    def __get_lang__(self, lang: str = '_ru', ) -> str:
        schema, field_name = self.varietal, 'name'
        if schema:
            prefix = getattr(schema, f'{field_name}{lang}') or getattr(schema, f'{field_name}')
            if self.percentage:
                prefix = f"{prefix} {int(round(self.percentage))}%"
            return prefix
        return None
"""


class DrinkVarietalLinkCreate(BaseModel):
    drink_id: int
    varietal_ids: List[int]  # полный список ID для связи


class DrinkVarietalLinkUpdate(BaseModel):
    varietal_ids: List[int]


"""
class DrinkDetailResponse(BaseModel):
    # not used
    id: int
    name: str
    # ... другие поля ...
    varietals: List[str]  # список __str__() значений

    class Config:
        from_attributes = True
"""
