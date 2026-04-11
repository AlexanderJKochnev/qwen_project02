# app.support.clickhouse.router.py
from typing import Optional
from app.support.clickhouse.repository import BeverageRepository
from app.support.clickhouse.service import EmbeddingService
from app.support.clickhouse.dependencies import get_embedding_service, get_repository
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/beverages", tags=["beverages"])


@router.post("/search")
async def search(
    query: str, category: Optional[str] = None, limit: int = 10, repo: BeverageRepository = Depends(get_repository),
    emb: EmbeddingService = Depends(get_embedding_service)
):
    # Получаем эмбеддинг запроса
    query_vec = await emb.encode_query(query)

    # Выполняем поиск
    results = await repo.vector_search(query_vec, category, limit)

    return {"query": query, "results": results}
