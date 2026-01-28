# app.support.outbox.router.py
"""
    тестирование подкючения к meilisearch

"""
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from meilisearch_python_sdk import AsyncClient
from app.core.config.database.meili_async import get_meili_client

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/meili-health")
async def check_meili_connection(
        client: AsyncClient = Depends(get_meili_client)
):
    """
    Диагностика асинхронного подключения к Meilisearch
    """
    logger.info("Debug: Проверка подключения к Meilisearch через DI...")

    try:
        # 1. Проверяем базовый Health API
        health = await client.health()

        # 2. Проверяем версию (это подтверждает, что API ключ валиден)
        version = await client.get_version()

        # 3. Проверяем доступность индексов (список ключей)
        indexes = await client.get_indexes()

        return {"status": "connected", "meili_status": health.status, "version": version.pkg_version,
                "total_indexes": len(indexes.results) if indexes else 0,
                "config": {"base_url": str(client.http_client.base_url), "timeout": str(client.http_client.timeout)}}

    except Exception as e:
        logger.exception(f"Debug Meili Error: {e}")
        raise HTTPException(
            status_code=503, detail={"error": str(e), "type": type(e).__name__,
                                     "suggestion": "Проверьте MEILISEARCH_URL в .env. Для локального запуска вне Docker используйте http://127.0.0.1:7700"}
        )
