# app.support.vintage.router.py
from fastapi import Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.vintage.model import VintageConfig, Designation, Classification
from app.support.vintage.repository import (ClassificationRepository, DesignationRepository,  # noqa: F401
                                            VintageConfigRepository)  # noqa: F401
from app.support.vintage.schemas import (VintageConfigUpdate, VintageConfigCreate, VintageConfigRead,
                                         DesignationUpdate, DesignationRead, DesignationCreate,
                                         ClassificationCreate, ClassificationUpdate, ClassificationRead)
from app.support.vintage.service import ClassificationService, DesignationService, VintageConfigService  # noqa: F401


class VintageConfigRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=VintageConfig,
            prefix="/vintage_config",
        )

    async def create(self, data: VintageConfigCreate,
                     session: AsyncSession = Depends(get_db)) -> VintageConfigRead:
        return await super().create(data, session)

    async def patch(self, id: int, data: VintageConfigUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> VintageConfigRead:
        return await super().patch(id, data, background_tasks, session)


class DesignationRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Designation,
            prefix="/designation",
        )

    async def create(self, data: DesignationCreate,
                     session: AsyncSession = Depends(get_db)) -> DesignationRead:
        return await super().create(data, session)

    async def patch(self, id: int, data: DesignationUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> DesignationRead:
        return await super().patch(id, data, background_tasks, session)


class ClassificationRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Classification,
            prefix="/classification",
        )

    async def create(self, data: ClassificationCreate,
                     session: AsyncSession = Depends(get_db)) -> ClassificationRead:
        return await super().create(data, session)

    async def patch(self, id: int, data: ClassificationUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> ClassificationRead:
        return await super().patch(id, data, background_tasks, session)
