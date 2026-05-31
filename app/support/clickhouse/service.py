# app/support/clickhouse/service.py
from typing import List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from app.core.services.service import Service
from app.core.types import ModelType
from app.core.utils.pydantic_utils import get_repo, get_service
from app.dependencies import get_clickhouse_repository_factory
from app.support import Food, Region, Varietal


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

    async def get_varietals(self, session: AsyncSession) -> List[dict]:
        raw_sql = """
                        SELECT
                            -- v_ch.id AS ch_id,
                            v_ch.name AS name
                        FROM default.pg_varietal AS v_ch
                        LEFT JOIN (
                            SELECT id, name
                            FROM drink_replica.varietals FINAL
                        ) AS v_pg
                            -- Применяем нормализацию текста к обеим таблицам
                            ON normalize_text(v_ch.name) = normalize_text(v_pg.name)
                        WHERE v_pg.name IS NULL OR v_pg.name = ''
                        AND name NOT LIKE '$%'
                  """
        data: List[dict] = await self.click_repo.run_raw_sql(raw_sql)
        model = Varietal
        if data:
            result: List[dict] = await self.bulk_create(data, model, session)
        else:
            result: List[dict] = [{'result': 'no data for import'}]
        return result

    async def get_foods(self, session: AsyncSession) -> List[dict]:
        raw_sql = """
                        SELECT
                            -- 1. Заменяем ' - ' на одиночный пробел, а затем схлопываем множественные пробелы в один
                            replaceRegexpAll(
                                replaceRegexpAll(v_ch.name, ' - ', ' '),
                                ' {2,}',
                                ' '
                            ) AS name
                        FROM default.pg_food AS v_ch
                        LEFT JOIN (
                            SELECT id, name
                            FROM drink_replica.foods FINAL
                        ) AS v_pg
                            ON normalize_text(v_ch.name) = normalize_text(v_pg.name)
                        WHERE
                            -- 2. Обязательно берем условия соединения в скобки, чтобы фильтр по '$' отработал корректно
                            (v_pg.name IS NULL OR v_pg.name = '')
                            -- Фильтруем артефакты, начинающиеся со знака доллара
                            AND v_ch.name NOT LIKE '$%'
                            -- На всякий случай отсекаем пустые строки, если они есть в справочнике
                            AND trimBoth(v_ch.name) != ''
                  """
        data: List[dict] = await self.click_repo.run_raw_sql(raw_sql)
        model = Food
        if data:
            result: List[dict] = await self.bulk_create(data, model, session)
        else:
            result: List[dict] = [{'result': 'no data for import'}]
        return result

    async def get_regions(self, session: AsyncSession) -> List[dict]:
        raw_sql = """
                        SELECT
                            ch_reg.name AS name,
                            pg_c.id AS country_id
                        FROM default.pg_region AS ch_reg
                        -- 1. Связываем регион ClickHouse с его временной страной
                        LEFT JOIN default.pg_country AS ch_c
                            ON ch_reg.country_id = ch_c.id
                        -- 2. Находим родной ID этой страны в реплике Postgres (с защитой от коллизии US)
                        LEFT JOIN (
                            SELECT
                                id,
                                multiIf(normalize_text(name) = 'united states', 'us', normalize_text(name)) AS norm_name
                            FROM drink_replica.countries FINAL
                        ) AS pg_c
                            ON normalize_text(ch_c.name) = pg_c.norm_name
                        -- 3. Проверяем, нет ли уже такого региона в этой стране в Postgres
                        LEFT JOIN (
                            SELECT id, name, country_id
                            FROM drink_replica.regions FINAL
                        ) AS pg_reg
                            ON normalize_text(ch_reg.name) = normalize_text(pg_reg.name)
                            AND pg_c.id = pg_reg.country_id
                        WHERE
                            -- Проверка на отсутствие дубликата в Postgres
                            (pg_reg.name IS NULL OR pg_reg.name = '')
                            -- Исключаем пустые строки
                            AND trimBoth(ch_reg.name) != ''
                            -- СТРОГАЯ ФИЛЬТРАЦИЯ МУСОРА (исключаем строки, начинающиеся с $)
                            AND ch_reg.name NOT LIKE '$%'
                            -- Гарантируем, что родительская страна уже добавлена в Postgres
                            AND pg_c.id IS NOT NULL
                            AND pg_c.id > 0
                  """
        data: List[dict] = await self.click_repo.run_raw_sql(raw_sql)
        model = Region
        if data:
            result: List[dict] = await self.bulk_create(data, model, session)
        else:
            result: List[dict] = [{'result': 'no data for import'}]
        return result