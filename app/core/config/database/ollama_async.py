# app.core.config.database.ollama_async.py

from typing import Optional, Any, Dict, List
# from fastapi import HTTPException
from ollama import AsyncClient
from ollama import ResponseError as OllamaResponseError
import httpx
import asyncio
from loguru import logger
from app.core.config.database.db_config import settings_db


OLLAMA_HOST = settings_db.OLLAMA_HOST  # Адрес в общей сети Docker
OLLAMA_TIMEOUT = settings_db.OLLAMA_TIMEOUT


class OllamaClientManager:
    """Менеджер для надежного управления подключением к Ollama."""

    def __init__(self, host: str, timeout: float = OLLAMA_TIMEOUT):
        self.host = host
        self.timeout = timeout
        self._client: Optional[AsyncClient] = None
        self._lock = asyncio.Lock()  # Блокировка для безопасного пересоздания клиента
        self._closed = False

    @property
    def client(self) -> Optional[AsyncClient]:
        """Прямой доступ к клиенту (для кастомных запросов)."""
        return self._client

    @property
    def is_connected(self) -> bool:
        """Флаг подключения (без проверки)."""
        return self._client is not None

    async def get_client(self) -> AsyncClient:
        """Возвращает существующего или создает нового клиента."""
        # Если клиент уже есть и работает, возвращаем его
        if self._client and await self._check_health(mute=True):
            logger.info('ollama client is already run')
            return self._client

        # Если клиента нет или он не работает, создаем нового под блокировкой
        async with self._lock:
            # Двойная проверка: пока ждали блокировку, другой запрос мог уже создать клиента
            if self._client and await self._check_health(mute=True):
                logger.info('another ollama client is already run')
                return self._client

            logger.info("Creating new Ollama client...")
            # Важно: закрываем старого клиента, если он был
            if self._client:
                await self._close_client()

            # Создаем нового клиента. Он внутри себя использует httpx.AsyncClient с пулом.
            self._client = AsyncClient(host=self.host, timeout=self.timeout)

            # Проверяем, что новый клиент действительно работает
            if not await self._check_health():
                self._client = None
                raise ConnectionError(f"Cannot connect to Ollama at {self.host}")

            logger.info("New Ollama client created and healthy.")
            return self._client

    async def _check_health(self, mute: bool = False) -> bool:
        """Проверяет, доступен ли Ollama сервис."""
        if not self._client:
            return False
        try:
            # Пытаемся получить список моделей как легкий healthcheck
            # await self.client.list()
            await self._client.list()
            if not mute:
                logger.success("Ollama connected")
            return True
        except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
            logger.warning(f"Health check failed: {e}")
            return False

    async def _close_client(self):
        """Корректно закрывает клиента."""
        if self._client:
            try:
                # Попытка закрыть клиента (важно для освобождения соединений)
                # У AsyncClient нет явного close, но он управляется через внутренний httpx-клиент.
                # При пересоздании старый клиент будет собран GC, но лучше обнулить ссылку.
                logger.info("Closing old client...")
            finally:
                self._client = None

    async def chat(self, **kwargs) -> Any:
        """
        Обертка для chat с автоматическими ретраями и обработкой ошибок.
        Принимает те же параметры, что и оригинальный client.chat()
        """
        max_retries = kwargs.pop('_max_retries', 2)
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                client = await self.get_client()
                return await client.chat(**kwargs)

            except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                last_error = e

                # Сбрасываем клиент при ошибке подключения
                async with self._lock:
                    self._client = None

                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff

            except OllamaResponseError as e:
                # Специфичные ошибки Ollama (модель не найдена и т.д.)
                logger.error(f"Ollama API error: {e}")
                raise

            except Exception as e:
                logger.error(f"Unexpected error in chat: {e}")
                raise

        raise ConnectionError(f"Failed after {max_retries + 1} attempts") from last_error

    async def generate(self, **kwargs) -> Any:
        """
        Обертка для generate с автоматическими ретраями и обработкой ошибок.
        Принимает те же параметры, что и оригинальный client.generate()
        """
        # logger.debug(f"generate called with kwargs: {kwargs}")
        max_retries = kwargs.pop('_max_retries', 2)
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                client = await self.get_client()
                return await client.generate(**kwargs)

            except (httpx.ConnectError, httpx.RemoteProtocolError) as e:
                logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                last_error = e

                async with self._lock:
                    self._client = None

                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)

            except OllamaResponseError as e:
                logger.error(f"Ollama API error: {e}")
                raise

            except Exception as e:
                logger.error(f"Unexpected error in generate: {e}")
                raise

        raise ConnectionError(f"Failed after {max_retries + 1} attempts") from last_error

    # === Прямой доступ к остальным методам ===

    async def list_models(self) -> List[str]:
        """Получить список доступных моделей (без ретраев)."""
        client = await self.get_client()
        response = await client.list()
        return [m.model for m in response.models]

    async def show_model(self, model: str) -> Dict:
        """Информация о модели."""
        client = await self.get_client()
        response = await client.show(model=model)
        return response.dict() if hasattr(response, 'dict') else dict(response)

    async def pull_model(self, model: str, **kwargs):
        """Скачать модель (может быть долгим)."""
        client = await self.get_client()
        # Для pull может быть стриминг
        return await client.pull(model=model)

    async def delete_model(self, model: str):
        """Удалить модель."""
        client = await self.get_client()
        return await client.delete(model=model)

    async def embed(self, **kwargs):
        """Получить эмбеддинги."""
        client = await self.get_client()
        return await client.embed(**kwargs)

    async def ps(self):
        """Список запущенных моделей."""
        client = await self.get_client()
        return await client.ps()

    # === Cleanup ===

    async def close(self):
        """Закрыть все ресурсы."""
        self._closed = True
        if self._check_health:
            await self._close_client()
        self._client = None
        logger.info("Ollama client manager closed")


_ollama_manager_instance = None


def get_ollama_manager(host: str = OLLAMA_HOST, timeout: float = OLLAMA_TIMEOUT) -> OllamaClientManager:
    """
    Функция для получения singleton экземпляра менеджера.
    """
    logger.warning('ollama_manager is deactivated')
    return
    global _ollama_manager_instance
    if _ollama_manager_instance is None:
        _ollama_manager_instance = OllamaClientManager(host=host, timeout=timeout)
        logger.success('first ollama_manager instance created')
    else:
        logger.info('ollama_manager instance is available now')
    return _ollama_manager_instance


# Для обратной совместимости оставляем переменную, но она теперь использует функцию
ollama_manager = get_ollama_manager()
