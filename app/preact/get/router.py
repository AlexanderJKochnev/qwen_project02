# app/support/get/router.py
"""
    роутер для DetailView для всех кроме Drink & Items
    выводит только словари  id: name
    по языкам
"""
from fastapi import Request, Depends
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from app.preact.core.router import PreactRouter
from app.core.config.database.db_async import get_db
from app.core.utils.pydantic_utils import get_pyschema
from app.core.config.project_config import settings
from app.core.utils.exception_handler import ValidationError_handler


class GetRouter(PreactRouter):
    def __init__(self):
        super().__init__(prefix='get', method='GET', tier=3)

    def __source_generator__(self, source: dict):
        """
        генератор для создания роутов
        """
        return ((f'/{key}' + '/{lang}/{id}',
                 get_pyschema(val, 'DetailView'),
                 None) for key, val in source.items())

    async def endpoint(self, request: Request, lang: str, id: int, session: AsyncSession = Depends(get_db)):
        try:
            current_path = request.url.path
            pref, lang = self.__path_decoder__(current_path, 3)
            model = self.source.get(pref)
            repo = self.get_repo(model)
            service = self.get_service(model)
            obj = await service.get_detail_view(lang, id, repo, model, session)
            return obj
        except ValidationError as exc:
            ValidationError_handler(exc)

    def _setup_routes_(self):
        # Add language endpoint first
        self.router.add_api_route('/languages', self.get_languages, methods=['GET'],
                                  tags=['system'], summary='Get available languages',
                                  openapi_extra={'request_model': None})
        # Then call parent method for other routes
        super()._setup_routes_()

    async def get_languages(self):
        """Return available languages from settings"""
        return {"languages": settings.LANGUAGES, "default": settings.DEFAULT_LANG}
