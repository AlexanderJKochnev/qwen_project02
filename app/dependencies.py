# app/dependencies.py
from functools import lru_cache
from typing import Any, Awaitable, Callable, Dict, Optional
from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from clickhouse_connect.driver.asyncclient import AsyncClient as ClickAsyncClient
from fastapi import Depends, Request


# from app.core.repositories.clickhouse_repository import ClickHouseRepositoryFactory
from app.core.utils.translation_utils import fill_missing_translations


@lru_cache()
async def get_ch_client(request: Request) -> ClickAsyncClient:
    """Получение асинхронного клиента ClickHouse."""
    client = request.app.state.ch_client
    if client is None:
        raise RuntimeError("ClickHouse client not initialized")
    return client  # ← это уже AsyncClient, не корутина!


async def get_clickhouse_repository_factory(
    client: ClickAsyncClient = Depends(get_ch_client)
) -> ClickHouseRepositoryFactory:
    """ Фабрика для работы с любыми таблицами.
        пример:
        repo_factory: ClickHouseRepositoryFactory = Depends(get_clickhouse_repository_factory)
        repo = repo_factory.for_table('images_metadata')
    """
    return ClickHouseRepositoryFactory(client)


def get_translator_func() -> Callable[[Dict[str, Any], Optional[bool]], Awaitable[Dict[str, Any]]]:
    return fill_missing_translations
