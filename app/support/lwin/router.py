# app.support.lwin.router.py
from fastapi import BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.lwin.model import Lwin
from app.support.lwin.service import LwinService
from app.support.lwin.schemas import LwinCreate, LwinRead, LwinUpdate


class LwinRouter(BaseRouter):
    def __init__(self):
        super().__init__(model=Lwin, prefix="/lwin")
        # self.service = LwinService

    async def create(self, data: LwinCreate, session: AsyncSession = Depends(get_db)) -> LwinRead:
        return await super().create(data, session)

    async def patch(self, id: int, data: LwinUpdate,
                    background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> LwinRead:
        return await super().patch(id, data, background_tasks, session)

    async def update_or_create(self, data: LwinCreate,
                               background_tasks: BackgroundTasks,
                               session: AsyncSession = Depends(get_db)) -> LwinRead:
        return await super().update_or_create(data, background_tasks, session)