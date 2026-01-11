# app/preact/core/router.py
"""
    базовый роутер для preact

"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Type
from app.core.models.base_model import DeclarativeBase
from app.core.utils.pydantic_utils import get_repo, get_service

from app.core.utils.alchemy_utils import get_lang_prefix
from app.auth.dependencies import get_active_user_or_internal
from app.core.config.database.db_async import get_db
# from app.core.config.project_config import settings
from app.support import (Category, Country, Food, Region, Subcategory, Subregion,
                         Superfood, Varietal, Sweetness)
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.services.service import Service


class PreactRouter:
    def __init__(self, prefix: str, method: str = 'GET', tier: int = 2):
        self.tags, self.prefix = [f'{prefix}'], f'/{prefix}'
        # self.languages = settings.LANGUAGES  # ['en', 'ru', 'fr', ...]
        self.tier = tier  # применяется в _path_decoder-
        self.method = method
        self.source = {'categories': Category,
                       'subcategories': Subcategory,
                       'countries': Country,
                       'regions': Region,
                       'subregions': Subregion,
                       'superfoods': Superfood,
                       'foods': Food,
                       'sweetness': Sweetness,
                       'varietals': Varietal
                       }
        self.router = APIRouter(prefix=self.prefix,
                                tags=self.tags,
                                dependencies=[Depends(get_active_user_or_internal)])
        self.schemas_generator(self.source)
        self._setup_routes_()

    def schemas_generator(self, source: dict, *args, **kwargs):
        """ генератор pydantic схем - overrride """
        pass

    def get_lang_prefix(self, lang: str):
        return get_lang_prefix(lang)

    def get_repo(self, model: Type[DeclarativeBase]) -> Type[Repository]:
        return get_repo(model)

    def get_service(self, model: Type[DeclarativeBase]) -> Type[Service]:
        return get_service(model)

    def _setup_routes_(self):
        for prefix, response_model, request_model in self.__source_generator__(self.source):
            self.router.add_api_route(prefix, endpoint=self.endpoint, methods=[self.method],
                                      response_model=response_model,
                                      openapi_extra={'request_model': request_model or None})

    def __source_generator__(self, source: dict):
        """
        генератор для создания роутов (path, schema) override it
        """
        return (self.__get_prepaire__(key, val) for key, val in source.items())

    def __path_decoder__(self, path: str, tier: int = 2):
        """ декодирует url.path справа"""
        result = path.rsplit('/', tier)
        lang = result[1 - tier]   # язык 'en', 'ru', 'fr' ...
        mod = result[0 - tier]    # self.source.key
        return mod, lang

    async def endpoint(self, request: Request, session: AsyncSession = Depends(get_db)):
        """ override it """
