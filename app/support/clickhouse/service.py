# app/support/clickhouse/service.py
from typing import List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from app.core.services.service import Service
from app.core.types import ModelType
from app.core.utils.pydantic_utils import get_repo, get_service
from app.dependencies import get_clickhouse_repository_factory
from app.support import Varietal


class ClickhouseImportService:
    def __init__(self,
                 click_repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory),
                 ):
        self.click_repo = click_repo_factory.for_table('raw_sql')

    async def bulk_create(self, data: List[dict], model: ModelType, session: AsyncSession):
        service: Service = get_service(model)
        repository = get_repo(model)
        result = []
        for data_dict in data:
            response: dict = await service.create(data_dict, repository, model, session)
            result.append(response)
        return result

    async def get_varietals(self, session: AsyncSession) -> dict:
        raw_sql = """
                        SELECT
                            -- v_ch.id AS ch_id,
                            v_ch.name AS name
                        FROM default.pg_varietal AS v_ch
                        LEFT JOIN (
                            -- Выбираем актуальные записи из Postgres, отсекая дубли модификатором FINAL
                            SELECT id, name
                            FROM drink_replica.varietals FINAL
                        ) AS v_pg
                            ON lower(trimBoth(v_ch.name)) = lower(trimBoth(v_pg.name))
                        -- Оставляем только те строки, которые не нашли совпадения в Postgres
                        WHERE (v_pg.name = '' OR v_pg.name IS NULL)
                        AND name NOT LIKE '$%'
                  """
        data: List[dict] = await self.click_repo.run_raw_sql(raw_sql)
        model = Varietal
        if data:
            result = await self.bulk_create(data, model, session)
        else:
            result = {'result': 'no data for import'}
        return result
