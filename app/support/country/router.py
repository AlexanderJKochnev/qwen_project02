# app/support/country/auth.py

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, BackgroundTasks
from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.country.model import Country
# from app.support.country.repository import CountryRepository
from app.support.country.schemas import (CountryRead, CountryCreate, CountryUpdate,
                                         CountryCreateRelation, CountryCreateResponseSchema)
# from app.support.country.service import CountryService


class CountryRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Country,
            prefix="/countries")

    async def create(self, data: CountryCreate, session: AsyncSession = Depends(get_db)) -> CountryCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int, data: CountryUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> CountryCreateResponseSchema:
        return await super().patch(id, data, background_tasks, session)

    async def create_relation(self, data: CountryCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> CountryRead:
        result = await super().create_relation(data, session)
        return result
