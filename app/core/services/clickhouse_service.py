# app.core.service.clickhouse_service.py
"""
    базовый сервисный слой для clickhouse
"""
from fastapi import Depends
from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from app.dependencies import get_clickhouse_repository_factory


class ClickHouseService:
    def __init__(self, table: str):
        self.repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory)

    def create(self, **kwargs):
        pass
        # override it
