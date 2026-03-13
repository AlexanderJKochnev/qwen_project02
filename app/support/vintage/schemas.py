# app.support.vintage.schemas.py
from app.core.schemas.base import (CreateSchema, ReadSchema, UpdateSchema,
                                   DetailView, ListView)
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


class VintageConfigCreate(CreateSchema):
    pass


class VintageConfigUpdate(UpdateSchema):
    pass


class VintageConfigRead(ReadSchema):
    pass


class VintageConfigDetailView(DetailView):
    pass


class VintageConfigListView(ListView):
    pass


class ClassificationCreate(CreateSchema):
    pass


class ClassificationUpdate(UpdateSchema):
    pass


class ClassificationRead(ReadSchema):
    pass


class ClassificationDetailView(DetailView):
    pass


class ClassificationListView(ListView):
    pass


class DesignationCreate(CreateSchema):
    pass


class DesignationUpdate(UpdateSchema):
    pass


class DesignationRead(ReadSchema):
    pass


class DesignationDetailView(DetailView):
    pass


class DesignationListView(ListView):
    pass
