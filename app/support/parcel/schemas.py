# app.support.parcel.schemas.py
from typing import Optional

from app.core.schemas.base import (CreateSchema, CreateSchemaSub, DetailView, ListView, ReadSchema, UpdateSchema)
from app.support.subregion.schemas import SubregionRead, SubregionCreateRelation

"""
1. Create
2. Update
3. Read
4. ListView - preact
5. DetailView - preact
6. ReadApiSchema - api
7. ReadRelation
8. CreateResponseSchema
9. CreateRelation - создание записей с зависимостями
10.CreateResponseSchema - Read + DateSchema
"""


class ParcelCreate(CreateSchema):
    pass


class ParcelUpdate(UpdateSchema):
    pass


class ParcelRead(ReadSchema):
    pass


class ParcelDetailView(DetailView):
    pass


class ParcelListView(ListView):
    pass


class SiteCreate(CreateSchema):
    subregion_id: Optional[int] = None


class SiteUpdate(UpdateSchema):
    subregion_id: Optional[int] = None


class SiteRead(ReadSchema):
    subregion: Optional[SubregionRead] = None


class SiteDetailView(DetailView):
    subregion: Optional[SubregionRead] = None


class SiteListView(DetailView):
    pass
    # subregion: Optional[SiteTitleRead] = None


class SiteCreateRelation(CreateSchemaSub):
    subregion: SubregionCreateRelation
