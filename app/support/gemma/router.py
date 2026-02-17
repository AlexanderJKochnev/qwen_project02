# app.support.gemma.router.py
from fastapi import APIRouter, Depends, Query
from typing import Callable
from app.auth.dependencies import get_active_user_or_internal
from app.core.utils.translation_utils import gemma_translate
from app.support.gemma.schemas import TranslationRequest
from app.support.gemma.service import TranslationService
from app.support.gemma.repository import OllamaRepository


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
        self.repo = OllamaRepository()
        self.service = TranslationService(self.repo)
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route("/translate", self.translate, methods=["GET"],
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/translate2", self.do_translate, methods=["GET"],
                                  openapi_extra={'x-request-schema': None})

    async def translate(
            self, text: str = Query(
                ..., description=("текст который нужно перевести")
            ), lang: str = Query('ru', description=("язык на который нужно перевести"))
    ) -> str:
        """  тестирование сервиса перевода Gemma.
             исходный язык должно определять автоматически
             язык на котороый перевести - либо 2-х значный код: ru en zh (н все языки)
             либо текстом russian, french...
        """
        return await gemma_translate(text, lang.lower())

    async def do_translate(self, params: TranslationRequest):
        """
        Экспериментируй с параметрами здесь!
        Gemma2:2b (level 1) — самая быстрая.
        Gemma2:9b (level 2) — самая точная для твоей RTX 3060.
        """
        result = await self.service.translate(params)
        return {"output": result, "config_used": params.dict(exclude={"text"})  # Возвращаем конфиг для контроля
                }
