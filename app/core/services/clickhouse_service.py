# app.core.service.clickhouse_service.py
"""
    базовый сервисный слой для clickhouse
    пока не понадобился - clickhouse работает с RAW SQL потому сразу из других service layer сразу в репозиторий
"""
from fastapi import Depends
from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from app.dependencies import get_clickhouse_repository_factory


class ClickHouseService:
    def __init__(self, table: str):
        pass
        # self.repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory)

    def create(self, **kwargs):
        pass
        # override it
