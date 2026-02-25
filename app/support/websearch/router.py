# app/support/websearch/router.py
from fastapi import APIRouter, Depends, status, Query
from typing import List, Dict, Callable
from app.auth.dependencies import get_active_user_or_internal
from app.support.websearch.service import get_web_search_service, WebSearchService
from app.support.websearch.schemas import SearchResponse, SearchRequest


prefix = 'websearch'
auth_dependency: Callable = get_active_user_or_internal
router = APIRouter(prefix=f"/{prefix}",
                   tags=[f"{prefix}"],
                   dependencies=[Depends(auth_dependency)],
                   include_in_schema=True)


# @router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search(request: SearchRequest, web_search: WebSearchService = Depends(get_web_search_service)):
    # 1. Сначала поиск в вашей PostgreSQL (полнотекстовый)
    # db_result = await search_in_postgres(request.query)  # ваша существующая функция

    # if db_result:
    #     return SearchResponse(
    #             found_in_db = True, description = db_result.description, location = db_result.location
    #             )

    # 2. Если в БД нет - веб-поиск
    search_results: List[Dict] = await web_search.search_searxng(request.query)

    if not search_results:
        return SearchResponse(
            found_in_db=False, description="Ничего не найдено в интернете"
        )
    return SearchResponse(found_in_db=False, result=search_results)

    # 3. LLM оценка и генерация
    llm_result = await web_search.llm_evaluate_and_summarize(
        request.query, search_results
    )

    return SearchResponse(
        found_in_db=False, description=llm_result.get("description"), location=llm_result.get("location"),
        confidence=llm_result.get("confidence")
    )


@router.get("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def searchX(search: str = Query(..., description=("что нужно найти")),
                  category: str = Query('general', description=("категория поиска")),
                  language: str = Query('en', description=("приоритетный язык поиска")),
                  max_results: int = Query(5, description=("кол-во результатов поиска")),
                  web_search: WebSearchService = Depends(get_web_search_service)):
    search_result: SearchResponse = await web_search.search_tune(search, category, language, max_results)
    return search_result
