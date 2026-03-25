# app.support.router.py

# app.suport.ollama.router.py
# from loguru import logger
from fastapi import Depends, HTTPException, Query, Body  # , BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enum import Preset, Prompts, Writers  # , LLmodel, Languages, Writers
from app.core.config.database.db_async import get_db
from app.core.routers.base import LightRouter
# from app.core.utils.common_utils import compare_lists_compact, jprint
# from app.support.ollama.model import Prompt, ISOLanguage, Proption, WriterRule
from app.support.vllm.service import VLLMService


class VllmRouter(LightRouter):
    """ языковые модели для OLLAMA"""

    def __init__(self):
        super().__init__(prefix="/vllm")
        self.VLLMservice = VLLMService()
        # self.service = VLLMService

    def setup_routes(self):
        self.router.add_api_route("/translate", self.get_translate,
                                  methods=["POST"],
                                  # response_model=List[LlmResponseSchema],
                                  openapi_extra={'x-request-schema': None})
        # super().setup_routes()

    async def get_translate(
            self, phrase: str = Body(
                ..., description="Текст для перевода.", title="текст для перевода",
                media_type="text/plain", ),
            # llmodel: LLmodel = Query('translategemma:latest', description="Имя модели в базе данных"),
            prompt: Prompts = Query('universal_translator', description="Имя промпта в базе данных"),
            proption: Preset = Query(None, description="Типовые настройки качество/скорость"),
            writer: Writers = Query(None, description="Типовые правила перевода"),
            langs: str = Query(
                'ru, en', description="Язык (языки) перевода двух-значные коды через "
                "запятую, например 'ru, fr, zh'"
            ), session: AsyncSession = Depends(get_db)
    ):
        """
           тестирование моделей для перевода:
           1. фраза для перевода
           2. prompt
           3. язык/языки для перевода
           возвращает:
        """
        try:
            result = await self.VLLMservice.get_translate(phrase, prompt, preset, writer, langs, session)
            return result
        except Exception as e:
            raise HTTPException(status_code=501, detail=e)
