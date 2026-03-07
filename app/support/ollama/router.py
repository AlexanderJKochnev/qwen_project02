# app.suport.ollama.router.py
from typing import List
from loguru import logger
from fastapi import BackgroundTasks, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.enum import Preset, Prompts, LLmodel, Languages
from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.core.utils.common_utils import compare_lists_compact, jprint
from app.support.ollama.model import Ollama, Prompt, ISOLanguage, Proption
from app.support.ollama.schemas import (LlmResponseSchema, OllamaCreate, PromptCreate,
                                        PromptRead, PromptUpdate,
                                        ISOLanguageCreate, ISOLanguageRead, ISOLanguageUpdate,
                                        ProptionRead, ProptionCreate, ProptionUpdate)
from app.support.ollama.service import LLMService, OllamaService


class OllamaRouter(BaseRouter):
    """ языковые модели для OLLAMA"""

    def __init__(self):
        super().__init__(model=Ollama, prefix="/ollama")
        self.LLMservice = LLMService()
        self.service = OllamaService

    def setup_routes(self):
        self.router.add_api_route("/llm", self.get_models_list,
                                  methods=["GET"],
                                  response_model=List[LlmResponseSchema],
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/llm/{model}", self.del_model, methods=['DELETE'])
        self.router.add_api_route("/translate", self.get_translate,
                                  methods=['POST'],
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/novel", self.get_novel,
                                  methods=['POST'],
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/full", self.get_full, methods=["GET"],
                                  response_model=self.nonpaginated_response,
                                  openapi_extra={'x-request-schema': None}
                                  )
        # super().setup_routes()

    async def del_model(self,
                        background_tasks: BackgroundTasks,
                        model_name: str = Query(..., description="Имя модели."),
                        session: AsyncSession = Depends(get_db)) -> bool:
        try:
            response: bool = await self.LLMservice.del_model(model_name)
            if response:
                await self.get_models_list(background_tasks, session)
            return response
        except Exception as e:
            raise HTTPException(status_code=501, detail=e)

    async def get_models_list(self, background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_db)):
        """
        получение списка загруженных моделей.
        сравнение с сохраненными данными в базе данных и обновление
        """
        try:
            response: List[dict] = await self.LLMservice.get_models_list()

            iter = 0
            while iter < 2:
                iter += 1
                #  валидирует исходные данные и возвращает плоский словарь
                result = [LlmResponseSchema.model_validate(key).model_dump() for key in response]
                result2 = await self.service.get_full(self.repo, self.model, session)
                result3 = (OllamaCreate(**key.to_dict()).model_dump() for key in result2)
                #  словарь с различиями added, removed, changed
                resp = compare_lists_compact(result3, result, 'model')
                if not resp:
                    return result
                # для remove <и changed> заменяем на id
                for key in ('removed', 'changed'):
                    if x := resp.get(key):
                        x = [b if key == 'removed' else (b, a)
                             for a in x for b in result2 if a['model'] == b.model]
                        resp[key] = x
                await self.service.maintain_llm_database(resp, self.repo, self.model, session)
            error = 'база данных ll моделей не может синхронизироваться с реально загруженными ll моделямии'
            logger.error(error)
            jprint(resp)
            raise Exception(error)
        except Exception as e:
            raise HTTPException(status_code=501, detail=e)

    async def get_translate(self, phrase: str = Field(None, description="Текст для перевода."),
                            llmodel: LLmodel = Query('translategemma:latest', description="Имя модели в базе данных"),
                            prompt: Prompts = Query('universal_translator', description="Имя промпта в базе данных"),
                            preset: Preset = Query(None, description="Типовые настройки качество/скорость"),
                            langs: str = Query('ru, en',
                                               description="Язык (языки) перевода двух-значные коды через "
                                                           "запятую, например 'ru, fr, zh'"),
                            session: AsyncSession = Depends(get_db)):
        """
           тестирование моделей для перевода:
           1. фраза для перевода
           2. модель LL выбирается наименьшая из всех с совпадающим именем
           3. prompt
           3. язык/языки для перевода
           возвращает:
        """
        try:
            result = await self.service.get_translate(phrase, llmodel, prompt, preset, langs, session)
            return result
        except Exception as e:
            raise HTTPException(status_code=501, detail=e)

    async def get_novel(
            self, phrase: str = Field(None, description="Наименование для описания (желательно на англ)."),
            llmodel: LLmodel = Query('qwen3:8b', description="Имя модели в базе данных"),
            prompt: Prompts = Query(None, description="Имя промпта в базе данных"),
            preset: Preset = Query(None, description="Типовые настройки качество/скорость"),
            langs: Languages = Query('ru', description="Язык текста 2-3 значный код"),
            session: AsyncSession = Depends(get_db)
    ) -> dict:
        """
           # тестирование моделей для генерации текста:
           ## 1. наименование для генерации описания
           ## 2. модель LL выбирается наименьшая из всех с совпадающим именем
           ## 3. prompt
        """
        try:
            result = await self.service.get_novel(phrase, llmodel, prompt, preset, langs, session)
            logger.warning(f'10. {result}')
            return result
        except Exception as e:
            raise HTTPException(status_code=501, detail=e)


class ISOLanguageRouter(BaseRouter):
    """ языки мира """

    def __init__(self):
        super().__init__(model=ISOLanguage, prefix="/isolanguage")

    def setup_routes(self):
        self.router.add_api_route(
            "/batch", self.batch_create, status_code=200, methods=['POST'],
            response_model=List[self.read_schema_relation],
            openapi_extra={'x-request-schema': f"List_{self.create_schema_relation.__name__}"}
        )
        super().setup_routes()

    async def create(self, data: ISOLanguageCreate, session: AsyncSession = Depends(get_db)) -> ISOLanguageRead:
        return await super().create(data, session)

    async def batch_create(self, data: List[ISOLanguageCreate],
                           session: AsyncSession = Depends(get_db)) -> List[ISOLanguageRead]:
        return await super().batch_create(data, session)

    async def patch(self, id: int, data: ISOLanguageUpdate,
                    background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> ISOLanguageRead:
        return await super().patch(id, data, background_tasks, session)


class PromptRouter(BaseRouter):
    """ промты для llm """

    def __init__(self):
        super().__init__(model=Prompt, prefix="/prompt")
        self.LLMservice = LLMService()

    def setup_routes(self):
        self.router.add_api_route("/translate", self.get_generate,
                                  methods=["GET"],
                                  # response_model=List[LlmResponseSchema]
                                  )
        super().setup_routes()

    async def create(self, data: PromptCreate, session: AsyncSession = Depends(get_db)) -> PromptRead:
        return await super().create(data, session)

    async def patch(self, id: int, data: PromptUpdate,
                    background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> PromptRead:
        return await super().patch(id, data, background_tasks, session)

    async def update_or_create(self, data: PromptCreate,
                               background_tasks: BackgroundTasks,
                               session: AsyncSession = Depends(get_db)) -> PromptRead:
        return await super().update_or_create(data, background_tasks, session)

    async def get_generate(self, translate_it: str = Query(None, description='текст, который нужно перевести'),
                           session: AsyncSession = Depends(get_db)):
        """
            Перевод текста

        """
        return translate_it


class ProptionRouter(BaseRouter):
    def __init__(self):
        super().__init__(model=Proption, prefix="/proption")

    async def create(self, data: ProptionCreate, session: AsyncSession = Depends(get_db)) -> ProptionRead:
        return await super().create(data, session)

    async def patch(self, id: int, data: ProptionUpdate,
                    background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> ProptionRead:
        return await super().patch(id, data, background_tasks, session)

    async def update_or_create(self, data: ProptionCreate,
                               background_tasks: BackgroundTasks,
                               session: AsyncSession = Depends(get_db)) -> ProptionRead:
        return await super().update_or_create(data, background_tasks, session)
