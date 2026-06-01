# app/support/clickhouse/service.py
from typing import List

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from app.core.services.service import Service
from app.core.types import ModelType
from app.core.utils.pydantic_utils import get_repo, get_service
from app.dependencies import get_clickhouse_repository_factory
from app.support import Food, Region, Subregion, Varietal


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
                    SELECT DISTINCT
                    -- 1. Берем чистое имя субрегиона из ClickHouse (без артефактов)
                    trimBoth(replaceRegexpAll(
                        replaceRegexpAll(ch_s.name, ' - ', ' '),
                        ' {2,}',
                        ' '
                    )) AS name,
                    -- 2. Находим РЕАЛЬНЫЙ ID региона в Postgres по текстовой цепочке через region_mapping
                    nullIf(rm.postgres_id, 0) AS region_id
                FROM default.pg_subregion AS ch_s
                -- Шаг А: Связываемся с регионами ClickHouse, чтобы узнать ТЕКСТОВОЕ имя родительского региона
                LEFT JOIN default.pg_region AS ch_reg
                    ON ch_s.region_id = ch_reg.id
                -- Шаг Б: Находим ID этого региона в Postgres строго по текстовому имени региона через готовую карту
                LEFT JOIN default.region_mapping AS rm
                    ON ch_reg.id = rm.click_id
                -- Шаг В: Ваш точный и надежный LEFT JOIN из вашего примера — ищем субрегион в Postgres ТУПО ПО ИМЕНИ
                LEFT JOIN (
                    SELECT name
                    FROM postgresql('wine_host:5432', 'wine_db', 'subregions', 'wine', 'wine1')
                    WHERE name IS NOT NULL AND trimBoth(name) != ''
                ) AS pg_s
                    ON ch_s.name = pg_s.name
                WHERE
                    -- Условие вашей выборки: субрегиона в Postgres вообще нет по имени
                    pg_s.name IS NULL
                    -- Фильтры мусора
                    AND ch_s.name NOT LIKE '$%'
                    AND ch_s.name IS NOT NULL
                    AND trimBoth(ch_s.name) != ''
                    AND ch_s.name NOT IN ('N/A', 'na', 'n/a', 'None')
                    -- Гарантируем, что родительский регион определился в Postgres, чтобы не нарушить Foreign Key
                    AND region_id IS NOT NULL
                  """
        data: List[dict] = await self.click_repo.run_raw_sql(raw_sql)
        # return data
        model = Subregion
        if data:
            result: List[dict] = await self.bulk_create(data, model, session)
        else:
            result: List[dict] = [{'result': 'no data for import'}]
        return result
