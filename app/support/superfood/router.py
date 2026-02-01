# app/support/superfood/router.py
from fastapi import Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.superfood.model import Superfood
from app.support.superfood.schemas import (SuperfoodCreate, SuperfoodRead,
                                           SuperfoodUpdate, SuperfoodCreateResponseSchema)


class SuperfoodRouter(BaseRouter):  # [SuperfoodCreate, SuperfoodUpdate, SuperfoodRead]):
    def __init__(self):
        super().__init__(
            model=Superfood,
            prefix="/superfoods",
        )

    async def create(self, data: SuperfoodCreate,
                     session: AsyncSession = Depends(get_db)) -> SuperfoodCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int, data: SuperfoodUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> SuperfoodCreateResponseSchema:
        return await super().patch(id, data, background_tasks, session)

    async def create_relation(self, data: SuperfoodCreate,
                              session: AsyncSession = Depends(get_db)) -> SuperfoodRead:
        result = await super().create_relation(data, session)
        return result
