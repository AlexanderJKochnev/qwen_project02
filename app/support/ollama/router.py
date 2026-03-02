# app.suport.ollama.router.py
from typing import List

from fastapi import BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.ollama.model import Ollama
from app.support.ollama.schemas import LlmResponseSchema, OllamaCreate, OllamaRead, OllamaUpdate
from app.support.ollama.service import LLMService, OllamaService
from app.core.utils.common_utils import compare_lists_compact


class OllamaRouter(BaseRouter):
    def __init__(self):
        super().__init__(model=Ollama, prefix="/ollama")
        self.service = OllamaService
        self.LLMservice = LLMService()

    def setup_routes(self):
        self.router.add_api_route("/llm", self.get_models_list,
                                  methods=["GET"],
                                  response_model=List[LlmResponseSchema])
        super().setup_routes()

    async def get_models_list(self, session: AsyncSession = Depends(get_db)):
        """
        получение списка загруженных моделей.
        сравнение с сохраненными данными в базе данных и обновление
        """
        response: List[dict] = await self.LLMservice.get_models_list()
        result = [LlmResponseSchema.model_validate(key).model_dump() for key in response]
        result2 = await self.service.get_full(self.repo, self.model, session)
        result3 = (OllamaCreate(**key.to_dict()).model_dump() for key in result2)
        #  словарь с различиями added, removed, changed
        from app.core.utils.common_utils import jprint
        resp = compare_lists_compact(result3, result, 'model')
        for key in ('removed', 'changed'):
            if x := resp.get(key):
                x = [b.id for a in x for b in result2 if a['model'] == b.model]
                jprint(x)
                resp[key] = x
        jprint(resp)
        return result

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
