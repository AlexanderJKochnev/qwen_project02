# app/support/producer/router.py
from fastapi import Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.producer.model import Producer, ProducerTitle
# from app.support.producer.repository import ProducerRepository
from app.support.producer.schemas import (ProducerCreate, ProducerRead, ProducerTitleCreate, ProducerTitleUpdate,
                                          ProducerTitleRead, ProducerUpdate, ProducerCreateRelation)
# from app.support.producer.service import ProducerService


class ProducerRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Producer,
            prefix="/producer",
        )

    async def create(self, data: ProducerCreate,
                     session: AsyncSession = Depends(get_db)):
        return await super().create(data, session)

    async def patch(self, id: int, data: ProducerUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)):
        return await super().patch(id, data, background_tasks, session)

    async def create_relation(self, data: ProducerCreateRelation,
                              session: AsyncSession = Depends(get_db)):
        result = await super().create_relation(data, session)
        return result


class ProducerTitleRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=ProducerTitle,
            prefix="/producer_title",
        )

    async def create(self, data: ProducerTitleCreate,
                     session: AsyncSession = Depends(get_db)):
        return await super().create(data, session)

    async def patch(self, id: int, data: ProducerTitleUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)):
        return await super().patch(id, data, background_tasks, session)
