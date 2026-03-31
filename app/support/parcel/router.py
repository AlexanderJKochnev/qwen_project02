# app.support.parcel.router.py
from fastapi import Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.parcel.model import Parcel, Site
# from app.support.parcel.repository import ProducerRepository
from app.support.parcel.schemas import (ParcelCreate, ParcelRead, SiteCreate, SiteUpdate,
                                        SiteRead, ParcelUpdate, SiteCreateRelation)
# импорт ниже инициализирует сервисы
from app.support.parcel.service import ParcelService, SiteService  # noqa: F401


class ParcelRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Parcel,
            prefix="/parcel",
        )

    async def create(self, data: ParcelCreate,
                     session: AsyncSession = Depends(get_db)):
        return await super().create(data, session)

    async def patch(self, id: int, data: ParcelUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)):
        return await super().patch(id, data, background_tasks, session)


class SiteRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Site,
            prefix="/site",
        )

    async def create(self, data: SiteCreate,
                     session: AsyncSession = Depends(get_db)):
        return await super().create(data, session)

    async def patch(self, id: int, data: SiteUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)):
        return await super().patch(id, data, background_tasks, session)

    async def create_relation(self, data: SiteCreateRelation,
                              session: AsyncSession = Depends(get_db)):
        result = await super().create_relation(data, session)
        return result
