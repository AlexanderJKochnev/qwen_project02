# app/core/routers/search_router.py
from decimal import Decimal
from typing import Optional, Union

from fastapi import Depends, Query, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.services.search_service import SearchService


class SearchRouter:
    """
        ставить перед BaseRouter
        mixin for base router. not for one alone using
        thus it have follows:
        self.model = model
        self.repo = get_repo(model)
        self.service: TService = get_service(model)
    """
    search_field = 'search_content'

    def setup_routes(self):
        self.router.add_api_route(
            "/find/search", self.search_items,
            methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        self.router.add_api_route(
            "/find/search_keyset", self.search_items_keyset,
            methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )

        # ---ниже подтягиваются остальные маршруты из базового роутера---
        next_method = getattr(super(), "setup_routes", None)
        if next_method:
            next_method()

    async def search_items(self, request: Request,
                           q: str = Query(None, min_length=1, description="Поисковый запрос"),
                           session: AsyncSession = Depends(get_db),
                           limit: int = Query(10, description="размер страницы"), **kwargs
                           ):
        repository = self.repo
        service = self.sevice  # SearchService
        model = self.model
        query_data = await service.search_items(request, q, limit, repository, model, session)
        return query_data

    async def search_items_keyset(self, request: Request, search_str: str = Query(
            None, description="Поисковый запрос (при отсутствии значения - выдает все записи?)"
    ), last_score: Optional[Union[Decimal, str, float]] = Query(
            None, description='similarity rate'
    ), last_id: Optional[int] = Query(None, description='last id (for preact)'),
        limit: int = Query(20, description='количество записей на страницу'),
        boost: float = Query(
        15.0, description="Премия за редкое слово "
        "(записи с редким словом из запроса попадают наверх выборки)"
    ), session: AsyncSession = Depends(get_db)
    ):
        """ постраничный поиск со смещением по keyset"""
        repository = self.repo
        service = SearchService
        model = self.model
        search_result = await service.search_items_keyset(search_str, limit, last_id, repository, model, session)
        return search_result
