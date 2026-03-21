# app/support/subregion/schemas.py

from typing import Optional

from app.core.schemas.base import (CreateResponse, CreateSchemaSub, FullSchema,
                                   ReadApiSchema, ReadSchema, UpdateSchema, DetailView, ListView)
from app.support.region.schemas import RegionCreateRelation, RegionReadApiSchema, RegionRead


class SubregionReadApiSchema(ReadApiSchema):
    region: Optional[RegionReadApiSchema] = None


class CustomCreateRelation:
    region: RegionCreateRelation


class CustomReadSchema:
    region: Optional[RegionRead] = None


class CustomCreateSchema:
    region_id: int


class CustomUpdSchema:
    region_id: Optional[int] = None


class SubregionRead(ReadSchema, CustomReadSchema):
    pass


class SubregionReadRelation(SubregionRead):
    pass


class SubregionCreate(CreateSchemaSub, CustomCreateSchema):
    pass


class SubregionCreateRelation(CreateSchemaSub, CustomCreateRelation):
    pass


class SubregionUpdate(UpdateSchema, CustomUpdSchema):
    pass


class SubregionFull(FullSchema, CustomReadSchema):
    pass


class SubregionCreateResponseSchema(SubregionCreate, CreateResponse):
    pass


class SubregionDetailView(DetailView):
    # region: Optional[RegionListView] = None
    pass


class SubregionListView(ListView):
    # region: Optional[RegionListView] = None
    pass
