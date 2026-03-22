# app/support/food/schemas.py

from typing import Optional
from app.core.schemas.base import (CreateResponse, CreateSchema, ReadSchema,
                                   UpdateSchema, DetailView, ListView, PkSchema)
from app.support.superfood.schemas import SuperfoodCreateRelation, SuperfoodRead


class CustomReadSchema:
    # superfood: Optional[SuperfoodRead] = None
    pass

class CustomCreateSchema:
    superfood_id: Optional[int] = None


class CustomCreateRelation:
    superfood: Optional[SuperfoodCreateRelation] = None


class CustomUpdSchema:
    superfood_id: Optional[int] = None
    # superfood: Optional[SuperfoodCreateRelation] = None


class FoodId(PkSchema):
    """
        для использования в CustomCreateDrinkItem
    """
    pass

class FoodRead(ReadSchema, CustomReadSchema):
    pass


class FoodReadRelation(FoodRead):
    pass


class FoodCreateRelation(CreateSchema, CustomCreateRelation):
    pass


class FoodCreate(CreateSchema, CustomCreateSchema):
    pass


class FoodUpdate(UpdateSchema, CustomUpdSchema):
    pass


class FoodCreateResponseSchema(FoodCreate, CreateResponse):
    pass


class FoodDetailView(DetailView):
    # superfood: Optional[ListView] = None
    pass


class FoodListView(ListView):
    # superfood: Optional[ListView] = None
    pass
