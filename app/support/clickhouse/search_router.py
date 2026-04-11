# app.support.clikhouse.search_router.py
from fastapi import APIRouter, Depends, BackgroundTasks

from app.support.clickhouse.dependencies import get_embedding_service, get_repository
from app.support.clickhouse.import_service.beverage_repository import BeverageRepository
# from app.support.clickhouse.repository import BeverageRepository
from app.support.clickhouse.import_service.schemas import RAGResponse, SearchQuery, SearchResult
from app.support.clickhouse.service import EmbeddingService

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=dict)
async def search(
        query: SearchQuery, repo: BeverageRepository = Depends(get_repository),
        embedding: EmbeddingService = Depends(get_embedding_service)
):
    """Семантический поиск"""
    query_vec = await embedding.encode_query(query.query)
    results = await repo.vector_search(
        query_embedding=query_vec, category=query.category, limit=query.limit
    )

    return {"query": query.query, "results": [SearchResult(
            name=r['name'], description=r['description'][:300], category=r['category'],
            country=r.get('country'), brand=r.get('brand'), price=r.get('price'), rating=r.get('rating'),
            similarity=1 - r.get('distance', 1)
            ) for r in results]}


@router.post("/rag", response_model=RAGResponse)
async def rag_generate(
        query: SearchQuery, background_tasks: BackgroundTasks, repo: BeverageRepository = Depends(get_repository),
        embedding: EmbeddingService = Depends(get_embedding_service)
):
    """RAG генерация"""
    query_vec = await embedding.encode_query(query.query)
    results = await repo.vector_search(query_vec, query.category, query.limit)

    # TODO: интеграция с LLM
    generated = f"Found {len(results)} relevant beverages. (LLM integration pending)"

    return RAGResponse(
        query=query.query, found=len(results), generated=generated, sources=[SearchResult(
            name=r['name'], description=r['description'][:300], category=r['category'],
            country=r.get('country'), brand=r.get('brand'), price=r.get('price'),
            rating=r.get('rating'), similarity=1 - r.get('distance', 1)
        ) for r in results]
    )
