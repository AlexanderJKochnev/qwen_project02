# app/support/region/router.py

from fastapi import Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.region.model import Region
from app.support.region.schemas import (RegionCreate, RegionRead, RegionUpdate, RegionCreateRelation,
                                        RegionCreateResponseSchema)


class RegionRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=Region,
            prefix="/regions",
        )
        self.create_response_schema = RegionRead

    """
    def setup_routes(self):
        # Настраивает маршруты
        self.router.add_api_route("", self.create, methods=["POST"], response_model=self.create_response_schema)
        self.router.add_api_route("", self.get, methods=["GET"], response_model=self.paginated_response)
        self.router.add_api_route("/{id}", self.get_one, methods=["GET"], response_model=self.read_schema)
        self.router.add_api_route("/{id}", self.patch, methods=["PATCH"], response_model=self.read_schema)
        self.router.add_api_route("/{id}", self.delete, methods=["DELETE"], response_model=self.delete_response)
    """

    async def create(self, data: RegionCreate,
                     session: AsyncSession = Depends(get_db)) -> RegionCreateResponseSchema:
        return await super().create(data, session)

    async def patch(self, id: int, data: RegionUpdate, background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> RegionCreateResponseSchema:
        return await super().patch(id, data, background_tasks, session)

    async def create_relation(self, data: RegionCreateRelation,
                              session: AsyncSession = Depends(get_db)) -> RegionRead:
        result = await super().create_relation(data, session)
        return result
