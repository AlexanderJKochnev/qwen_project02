# app/support/subregion/router.py

from fastapi import Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.subregion.model import Subregion
from app.support.subregion.schemas import (SubregionCreate, SubregionUpdate,
                                           SubregionCreateRelation, SubregionCreateResponseSchema)


class SubregionRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Subregion,
            prefix="/subregions",
        )
        """self.create_response_schema = SubregionRead
        try:
            self.setup_routes()
        except Exception as e:
            print(f'===============subregion routert error {e}==========')
        """

    async def create(self, data: SubregionCreate,
                     session: AsyncSession = Depends(get_db)) -> SubregionCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int, data: SubregionUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> SubregionCreateResponseSchema:
        return await super().patch(id, data, background_tasks, session)

    async def create_relation(self, data: SubregionCreateRelation,
                              session: AsyncSession = Depends(get_db)):
        result = await super().create_relation(data, session)
        return result
