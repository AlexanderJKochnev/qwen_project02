# app.support.clickhouse.router.py
from typing import Optional

from app.core.config.database.click_async import get_ch_client
from app.support.clickhouse.repository import BeverageRepository
from app.support.clickhouse.service import embedding_service, EmbeddingService
from app.core.enum import Rag_category
from app.support.clickhouse.dependencies import get_embedding_service, get_repository
from fastapi import APIRouter, Depends, Query

router = APIRouter(prefix="/beverages", tags=["beverages"])


@router.get("/search")
async def search_beverages(
        q: str = Query(..., description="Поисковый запрос"),
        category: Rag_category = Query(None, description="Категория, если есть"),
        ch_client=Depends(get_ch_client)  # Ваша зависимость из ClickHouseManager
):
    # 1. Получаем вектор 384d на CPU (займет ~15-20мс)
    query_vector = embedding_service.get_query_embedding(q)

    # 2. Ищем в ClickHouse (индекс HNSW подхватится автоматически)
    repo = BeverageRepository(ch_client)
    results = await repo.vector_search(
        query_embedding=query_vector, category=category, limit=10
    )

    return {"results": results}
