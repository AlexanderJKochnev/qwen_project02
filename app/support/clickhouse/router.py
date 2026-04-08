# app.support.clickhouse.router.py
import json

from fastapi import Depends, File, Form, HTTPException, Path, Query, status, UploadFile, BackgroundTasks
from pydantic import ValidationError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.dependencies import get_active_user_or_internal
from app.core.config.database.click_async import get_ch_client
from app.core.config.database.db_async import get_db
from app.core.config.project_config import get_paging
from app.core.routers.base import LightRouter
from app.core.services.click_service import ClickService
from app.mongodb.service import ThumbnailImageService
from app.support.item.model import Item
from app.support.item.repository import ItemRepository
from app.core.enum import CliSearchMode

paging = get_paging


class ClickHouseRouter(LightRouter):
    def __init__(self, prefix: str = '/clickhouse',
                 **kwargs):
        self.service = ClickService

    def setup_routes(self):
        self.router.add_api_route(
            "/import_csv", self.import_csv, status_code=status.HTTP_200_OK, methods=["POST"],
            openapi_extra={'x-request-schema': None}
        )

    async def import_csv(self, background_tasks: BackgroundTasks,
                         ch_client=Depends(get_ch_client), session=Depends(get_db)):
        """
        Импорт CSV с использованием GPU для эмбеддингов.
        GPU модель загружается временно, после импорта выгружается.
        """
        return await self.service.import_csv()
