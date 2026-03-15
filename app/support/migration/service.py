# app.support.migration.service
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.services.service import Service
from app.core.types import ModelType


class MigrationService(Service):
    pass

    async def tier_one(self, session: AsyncSession) -> dict:
        pass
        return {'result': True}