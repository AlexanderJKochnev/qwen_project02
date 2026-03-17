# app.support.source.schemas.py
from app.core.schemas.base import (CreateSchema, DetailView, ListView, ReadSchema, UpdateSchema)

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


class SourceCreate(CreateSchema):
    pass


class SourceUpdate(UpdateSchema):
    pass


class SourceRead(ReadSchema):
    pass


class SourceDetailView(DetailView):
    pass


class SourceListView(ListView):
    pass

class SourceCreateRelation(SourceDetailView):
    pass