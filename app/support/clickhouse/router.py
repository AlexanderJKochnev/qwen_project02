# app/support/clickhouse/router.py

from fastapi import APIRouter, Depends, Path, Query, Request
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
        self.service = ClickhouseImportService()
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route(
            "/varietal", self.get_varietal, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )

    async def get_varietal(self, session: AsyncSession = Depends(get_db)):
        result = await self.service.get_varietals()
        return result