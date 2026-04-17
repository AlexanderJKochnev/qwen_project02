from typing import Optional, List, Dict
from fastapi import APIRouter, Depends, Query
from loguru import logger

from app.core.config.database.click_async import get_ch_client
from app.support.clickhouse.service import embedding_service
from app.support.clickhouse.repository import BeverageRepository
from app.core.enum import Rag_category

router = APIRouter(prefix="/beverages", tags=["beverages"])


@router.get("/get")
async def get(page: int = 1, page_size: int = 20, ch_client=Depends(get_ch_client)):
    skip = (page - 1) * page_size
    repo = BeverageRepository(ch_client)
    result = await repo.get_word_hash(skip, page_size)
    return result


@router.get("/search")
async def search_beverages(
        q: str = Query(..., description="Поисковый запрос (просто текст)"),
        category: Optional[Rag_category] = Query(None, description="Категория для фильтрации"),
        ch_client=Depends(get_ch_client)
):
    # 1. Получаем вектор 256d.
    # StaticModel не требует префиксов — подаем чистый текст запроса.
    query_vector = embedding_service.get_query_embedding(q)

    if not query_vector:
        return {"results": [], "status": "error", "message": "Failed to generate embedding"}

    # 2. Инициализируем репозиторий
    repo = BeverageRepository(ch_client)

    # 3. Поиск. Внутри репозитория должен быть zip(column_names, row)
    # для обработки поколоночного вывода ClickHouse.
    results = await repo.vector_search(
        query_embedding=query_vector, category=category.value if category else None, limit=10
    )

    return {"results": results}
