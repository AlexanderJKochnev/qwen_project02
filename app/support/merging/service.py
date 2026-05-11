# app.support.merging.service.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from app.dependencies import get_clickhouse_repository_factory
from app.support.drink.repository import DrinkRepository


class MergingService:
    def __init__(self, session: AsyncSession = Depends(get_db),
                 click_repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory),
                 ):
        self.session = session
        self.click_repo = click_repo_factory.for_table('drinks_lwins')
        # logger.warning(f"DEBUG: repo.client type = {type(self.click_repo.client)}")  # Должно быть AsyncClient
        self.repository = DrinkRepository

    async def get_drinks_lwins(self):
        result = await self.click_repo.get_all(order_by='id', fields=['id', 'id_old', 'dict'])
        return result
