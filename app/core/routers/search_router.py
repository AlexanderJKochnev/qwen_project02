# app/core/routers/search_router.py
from fastapi import Depends, Query, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.services.search_service import SearchService
from app.core.types import ModelType


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
            "/search/{q}", self.search_items,
            methods=["GET"],
            openapi_extra={'x-request-schema': None}
        )
        # ---ниже подтягиваются остальные маршруты из базового роутера---
        next_method = getattr(super(), "setup_routes", None)
        if next_method:
            next_method()

    async def search_items(self, request: Request,
                           q: str = Path(..., min_length=1, description="Поисковый запрос"),
                           session: AsyncSession = Depends(get_db),
                           limit: int = Query(10, description="размер страницы")
                           ):
        repository = self.repo
        service = SearchService
        model = self.model
        query_data = await service.search_items(request, q, limit, repository, model, session)
        