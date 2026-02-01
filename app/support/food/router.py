# app/support/food/auth.py

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, BackgroundTasks
from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.food.model import Food
from app.support.food.schemas import (FoodRead, FoodCreate, FoodUpdate, FoodCreateRelation,
                                      FoodCreateResponseSchema)


class FoodRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Food,
            prefix="/foods",
        )

    async def create(self, data: FoodCreate,
                     session: AsyncSession = Depends(get_db)) -> FoodCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int, data: FoodUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> FoodCreateResponseSchema:
        return await super().patch(id, data, background_tasks, session)

    async def create_relation(self, data: FoodCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> FoodRead:
        result = await super().create_relation(data, session)
        return result
