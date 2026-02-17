# app.support.gemma.router.py
from fastapi import APIRouter, Depends, Query
from typing import Callable
from app.auth.dependencies import get_active_user_or_internal
from app.core.utils.translation_utils import gemma_translate


class GemmaRouter:
    def __init__(
        self,
        prefix: str = '/gemma',
        auth_dependency: Callable = get_active_user_or_internal,
        **kwargs
    ):
        self.auth_dependency = auth_dependency
        self.prefix = prefix
        self.tags = [prefix.replace('/', '')]
        include_in_schema = kwargs.get('include_in_schema', True)
        self.router = APIRouter(prefix=prefix,
                                tags=self.tags,
                                dependencies=[Depends(self.auth_dependency)],
                                include_in_schema=include_in_schema)
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route("/translate", self.translate, methods=["GET"],
                                  openapi_extra={'x-request-schema': None})

    async def translate(self,
                        text: str = Query(...,
                                          description=("текст котолрый нужнол перевести")),
                        lang: str = Query('ru', description=("язык на который нужно перевести"))
                        ) -> str:
        """  тестирование сервиса перевода Gemma.
             исходный язык должно определять автоматически
             язык на котороый перевсти - либо 2-х значный код: ru en zh (н все языки)
             либо текстом russian, french...
        """
        return gemma_translate(text, lang.lower())
