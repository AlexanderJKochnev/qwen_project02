# app/support/warehouse/schemas.py
from typing import Optional

from app.core.schemas.base import (CreateSchema, FullSchema, ReadSchema,
                                   UpdateSchema, CreateResponse)
from app.support.customer.schemas import CustomerCreate


class CustomCreateRelation:
    customer: CustomerCreate


class CustomReadSchema:
    address: Optional[str] = None
    # customer: Optional[str] = None
    id: int


class CustomCreateSchema:
    address: Optional[str] = None
    customer_id: int  # = Field(..., description="customer ID (Customer.id) для связи Many-to-One")


class CustomUpdSchema:
    address: Optional[str] = None
    customer_id: Optional[int] = None


class WarehouseRead(ReadSchema, CustomReadSchema):
    pass


class WarehouseReadRelation(ReadSchema, CustomReadSchema):
    pass


class WarehouseCreate(CreateSchema, CustomCreateSchema):
    pass


class WarehouseCreateRelation(CreateSchema, CustomCreateRelation):
    pass


class WarehouseUpdate(UpdateSchema, CustomUpdSchema):
    pass


class WarehouseFull(FullSchema, CustomReadSchema):
    pass


class WarehouseCreateResponseSchema(WarehouseCreate, CreateResponse):
    pass
