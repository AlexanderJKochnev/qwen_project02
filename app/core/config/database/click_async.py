# app.core.config.database.click_async.py
import clickhouse_connect
from app.core.config.project_config import settings
from fastapi import Request


class ClickHouseManager:
    def __init__(self):
        self.host = settings.CH_HOST
        self.port = settings.CH_PORT
        self.user = settings.CH_USER
        self.password = settings.CH_PASSWORD
        self.client = None

    async def connect(self):
        # Создаем асинхронный клиент
        # Настройка 'max_connections' важна для FastAPI под нагрузкой
        self.client = await clickhouse_connect.get_async_client(
            host=self.host,
            port=self.port,
            username=self.user,
            password=self.password,
            # Опционально: сжатие данных для ускорения сети
            compress=True
        )
        return self.client

    async def close(self):
        if self.client:
            await self.client.close()

# Зависимость (Dependency Injection) для получения клиента в эндпоинтах


async def get_ch_client(request: Request):
    return request.app.state.ch_client
