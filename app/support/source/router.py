# app.support.source.router.py

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, BackgroundTasks
from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.source.model import Source
from app.support.source.service import SourceService  # noqa: F401
from app.support.source.schemas import (SourceRead, SourceCreate, SourceUpdate)


class SourceRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Source,
            prefix="/source",
        )

    async def create(self, data: SourceCreate,
                     session: AsyncSession = Depends(get_db)) -> SourceRead:
        return await super().create(data, session)

    async def patch(self, id: int,
                    data: SourceUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> SourceRead:
        return await super().patch(id, data, background_tasks, session)
