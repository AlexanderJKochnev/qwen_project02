# app/support/producer/schemas.py
from typing import Optional
from app.core.schemas.base import (CreateSchema, ReadSchema, UpdateSchema,
                                   DetailView, ListView, CreateSchemaSub)
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


class ProducerTitleCreate(CreateSchema):
    pass


class ProducerTitleUpdate(UpdateSchema):
    pass


class ProducerTitleRead(ReadSchema):
    pass


class ProducerTitleDetailView(DetailView):
    pass


class ProducerTitleListView(ListView):
    pass


class ProducerCreate(CreateSchema):
    producertitle_id: Optional[int] = None


class ProducerUpdate(UpdateSchema):
    producertitle_id: Optional[int] = None


class ProducerRead(ReadSchema):
    producertitle: Optional[ProducerTitleRead] = None


class ProducerDetailView(DetailView):
    producertitle: Optional[ProducerTitleRead] = None


class ProducerListView(ListView):
    pass
    # producertitle: Optional[ProducerTitleRead] = None


class ProducerCreateRelation(CreateSchemaSub):
    producertitle: ProducerTitleCreate
