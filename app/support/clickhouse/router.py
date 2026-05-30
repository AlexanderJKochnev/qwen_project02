# app/support/clickhouse/router.py

from fastapi import APIRouter, Depends, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_active_user_or_internal
from app.core.config.database.db_async import get_db
"""


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
            "/generator/{id}", self.test_generate_image_by_text, methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
