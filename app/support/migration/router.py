# app.support.migration.router

from fastapi import Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.migration.model import Migration
from app.support.migration.repository import MigrationRepository  # NOQA: F401
# from app.support.migration.schemas import (MigrationCreate, MigrationRead,  # MigrationCreateRelation,
#                                           MigrationUpdate, MigrationCreateResponseSchema)
from app.support.migration.service import MigrationService   # NOQA: F401


class MigrationRouter(BaseRouter):  # [MigrationCreate, MigrationUpdate, MigrationRead]):
    def __init__(self):
        super().__init__(
            model=Migration,
            prefix="/migrations",
        )

    def setup_routes(self):
        """Настраивает маршруты"""
        self.router.add_api_route("", self.tier_one, methods=["GET"],
                                  # response_model=self.create_response_schema,
                                  openapi_extra={'x-request-schema': self.create_schema.__name__})

    async def tier_one(self, session: AsyncSession = Depends(get_db)) -> dict:
        """
            выполнение действия имплементации:
        """
        result = await self.service.tier_one(self.repo, self.model, session)
        if result is None:
            raise HTTPException(status_code=500, detail=f'неведомая ошибка')
        return result


