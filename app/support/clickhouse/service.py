# app/support/clickhouse/service.py
from fastapi import Depends

from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from app.dependencies import get_clickhouse_repository_factory


class ClickhouseImportService:
    def __init__(self,
                 click_repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory),
                 ):
        self.click_repo = click_repo_factory.for_table('raw_sql')

    async def get_varietals(self) -> dict:
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
                        AND new_varietal_name NOT LIKE '$%'
                  """
        result: dict = await self.click_repo.run_raw_sql(raw_sql)
        
        return result
