# app/support/clickhouse/router.py
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_active_user_or_internal
from app.core.config.database.db_async import get_db
from app.support.clickhouse.service import ClickhouseImportService

"""
    импорт данных из clickhouse
"""


class ClickImportRouter:
    def __init__(self):
        prefix = 'click_import'
        self.tags, self.prefix = [f'{prefix}'], f'/{prefix}'
        self.router = APIRouter(
            prefix=self.prefix, tags=self.tags, dependencies=[Depends(get_active_user_or_internal)]
        )
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route(
            "/varietal", self.get_varietal, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/food", self.get_food, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )

    async def get_varietal(self, session: AsyncSession = Depends(get_db),
                           click_service: ClickhouseImportService = Depends()):
        result: List[dict] = await click_service.get_varietals(session)
        return result

    async def get_food(self, session: AsyncSession = Depends(get_db),
                       click_service: ClickhouseImportService = Depends()):
        result: List[dict] = await click_service.get_foods(session)
        return result
