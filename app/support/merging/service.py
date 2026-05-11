# app.support.merging.service.py
from typing import Dict, List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.config.database.db_async import get_db
from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from app.core.utils.pydantic_utils import list_dict
from app.dependencies import get_clickhouse_repository_factory
from app.support.merging.repository import MergingRepository
from app.support.drink.model import Drink


class MergingService:
    def __init__(self, session: AsyncSession = Depends(get_db),
                 click_repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory),
                 ):
        self.session = session
        self.click_repo = click_repo_factory.for_table('drinks_lwins')
        # logger.warning(f"DEBUG: repo.client type = {type(self.click_repo.client)}")  # Должно быть AsyncClient
        self.repository = MergingRepository

    async def get_drinks_lwins(self):
        """
        {
          "id": 1,
          "id_old": 109324,
          "dict": 0.2876712381839752
        },
        """
        result: List[Dict] = await self.click_repo.get_all(order_by='id', fields=['id', 'id_old', 'dict'])
        return result

    async def get_drinks_data(self):
        """
        получает данные по id
        """
        chunk = 200
        response = await self.get_drinks_lwins()
        if not response:
            return
        source = {val['id']: val['id_old'] for val in response}
        ids = tuple(source.keys())
        result: List = self.repository.get_drinks_by_ids(ids, self.session)
        return list_dict(result)
