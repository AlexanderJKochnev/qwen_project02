# app/support/warehouse/auth.py
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.warehouse.model import Warehouse
# from app.support.warehouse.repository import WarehouseRepository
from app.support.warehouse.schemas import (WarehouseRead, WarehouseCreate, WarehouseUpdate,
                                           WarehouseCreateRelation, WarehouseCreateResponseSchema)
# from app.support.warehouse.service import WarehouseService


class WarehouseRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Warehouse,
            prefix="/warehouses",
            # tags=["warehouses"],
            # service=WarehouseService,
            # create_schema_relation=WarehouseCreateRelation,
            # create_response_schema=WarehouseCreateResponseSchema
        )

    async def create(self, data: WarehouseCreate,
                     session: AsyncSession = Depends(get_db)) -> WarehouseCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int, data: WarehouseUpdate,
                    session: AsyncSession = Depends(get_db)) -> WarehouseCreateResponseSchema:
        return await super().patch(id, data, session)

    async def create_relation(self, data: WarehouseCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> WarehouseRead:
        result = await super().create_relation(data, session)
        return result
