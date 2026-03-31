# app/support/category/router.py
from fastapi import BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.category.model import Category
# from app.support.category.repository import CategoryRepository
from app.support.category.schemas import (CategoryCreate,  # CategoryCreateRelation,
                                          CategoryUpdate)


# from app.support.category.service import CategoryService


class CategoryRouter(BaseRouter):  # [CategoryCreate, CategoryUpdate, CategoryRead]):
    def __init__(self):
        super().__init__(
            model=Category,
            prefix="/categories",
        )

    async def create(self, data: CategoryCreate,
                     session: AsyncSession = Depends(get_db)):
        return await super().create(data, session)

    async def patch(self, id: int, data: CategoryUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)):
        return await super().patch(id, data, background_tasks, session)

    async def create_relation(self, data: CategoryCreate,
                              session: AsyncSession = Depends(get_db)):
        result = await super().create_relation(data, session)
        return result
