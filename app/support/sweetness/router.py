# app/support/sweetness/auth.py

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.sweetness.model import Sweetness
from app.support.sweetness.schemas import (SweetnessRead, SweetnessCreate,
                                           SweetnessUpdate, SweetnessCreateRelation, SweetnessCreateResponseSchema)


class SweetnessRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Sweetness,
            prefix="/sweetness",
        )

    async def create(self, data: SweetnessCreate,
                     session: AsyncSession = Depends(get_db)) -> SweetnessCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int, data: SweetnessUpdate,
                    session: AsyncSession = Depends(get_db)) -> SweetnessCreateResponseSchema:
        return await super().patch(id, data, session)

    async def create_relation(self, data: SweetnessCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> SweetnessRead:
        result = await super().create_relation(data, session)
        return result
