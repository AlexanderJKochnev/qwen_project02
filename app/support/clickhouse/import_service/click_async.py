# app.support.clickhouse.import_service.click_async.py
from typing import Optional

import clickhouse_connect
from app.support.clickhouse.import_service.project_config import settings
from fastapi import Request
from loguru import logger
from contextlib import asynccontextmanager


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
