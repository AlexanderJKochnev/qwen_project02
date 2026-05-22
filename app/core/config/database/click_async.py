# app.core.config.database.click_async.py
from contextlib import asynccontextmanager
from typing import Optional

import clickhouse_connect
from fastapi import Request
from loguru import logger
from pypika import CustomFunction, Query, Table  # , functions as fn, CustomFunction

from app.core.config.project_config import settings


class ClickHouseManager:
    def __init__(self):
        self.host = settings.CH_HOST
        self.port = settings.CH_PORT
        self.user = settings.CH_USER
        self.password = settings.CH_PASSWORD
        self._client: Optional[clickhouse_connect.driver.asyncclient.AsyncClient] = None

    async def connect(self):
        # Создаем асинхронный клиент
        # Настройка 'max_connections' важна для FastAPI под нагрузкой
        self._client = await clickhouse_connect.get_async_client(
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            # Опционально: сжатие данных для ускорения сети
            compress=True,
            # connect_timeout=30,
            # send_receive_timeout=30
        )
        return self._client

    async def close(self):
        if self._client:
            await self._client.close()

    @property
    def client(self):
        if not self._client:
            raise RuntimeError("ClickHouse not connected")
        return self._client


# Зависимость (Dependency Injection) для получения клиента в эндпоинтах


async def get_ch_client(request: Request):
    return request.app.state.ch_client


@asynccontextmanager
async def get_ch_session():
    """Контекстный менеджер для сессии (для фоновых задач)"""
    client = await get_ch_client()
    try:
        yield client
    except Exception as e:
        logger.error(f"Session error: {e}")
        raise


# получение заглушки для изображений
async def get_dump(client: clickhouse_connect.driver.asyncclient.AsyncClient) -> tuple:
    """
        получение заглушки для изображений - сделано здесь что-бы не тащить лишние импорты в main.py
        данные жестко зашиты в код - можно вынести в .env
    """
    # Первый аргумент — имя функции в ClickHouse, второй — параметры
    try:
        tag_value: str = "dump001"
        fields: list = ['fid', 'fid_thumb']
        order_by: str = 'tags'
        has_token_func = CustomFunction('hasAllTokens', ['field', 'token'])
        events = Table('images_metadata_active')
        q = Query.from_(events).select(*(events[k] for k in fields))
        q = q.where(has_token_func(events['tags'], tag_value)).orderby(order_by)
        q = q.limit(1)
        result = await client.query(q.get_sql())
        res: dict = result.first_item if result.row_count > 0 else None
        print(tuple(res.values()))
        return tuple(res.values())
    except Exception as e:
        logger.error(f'app.core.config.database.click_async.get_dump {e}')
        return None