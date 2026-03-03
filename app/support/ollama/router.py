# app.suport.ollama.router.py
from typing import List
from loguru import logger
from fastapi import BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.core.utils.common_utils import compare_lists_compact, jprint
from app.support.ollama.model import Ollama, Prompt, ISOLanguage
from app.support.ollama.schemas import (LlmResponseSchema, OllamaCreate, OllamaRead, OllamaUpdate, PromptCreate,
                                        PromptRead, PromptUpdate,
                                        ISOLanguageCreate, ISOLanguageRead, ISOLanguageUpdate)
from app.support.ollama.service import LLMService


class OllamaRouter(BaseRouter):
    def __init__(self):
        super().__init__(model=Ollama, prefix="/ollama")
        self.LLMservice = LLMService()

    def setup_routes(self):
        self.router.add_api_route("/llm", self.get_models_list,
                                  methods=["GET"],
                                  response_model=List[LlmResponseSchema])
        super().setup_routes()

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

    async def create(self, data: OllamaCreate, session: AsyncSession = Depends(get_db)) -> OllamaRead:
        return await super().create(data, session)

    async def patch(self, id: int, data: OllamaUpdate,
                    background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> OllamaRead:
        return await super().patch(id, data, background_tasks, session)

    async def update_or_create(self, data: OllamaUpdate,
                               background_tasks: BackgroundTasks,
                               session: AsyncSession = Depends(get_db)) -> OllamaRead:
        return await super().update_or_create(data, background_tasks, session)


class ISOLanguageRouter(BaseRouter):
    def __init__(self):
        super().__init__(model=ISOLanguage, prefix="/isolanguage", batch=True)

    async def create(self, data: ISOLanguageCreate, session: AsyncSession = Depends(get_db)) -> ISOLanguageRead:
        return await super().create(data, session)

    async def patch(self, id: int, data: ISOLanguageUpdate,
                    background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> ISOLanguageRead:
        return await super().patch(id, data, background_tasks, session)


class PromptRouter(BaseRouter):
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
