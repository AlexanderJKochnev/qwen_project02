# app.suport.ollama.router.py
from typing import List

from fastapi import BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.database.db_async import get_db
from app.core.routers.base import BaseRouter
from app.support.ollama.model import Ollama
from app.support.ollama.schemas import LlmResponseSchema, OllamaCreate, OllamaRead, OllamaUpdate
from app.support.ollama.service import LLMService, OllamaService


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

    async def get_models_list(self):
        """
        получение загруженных моделей
        """
        response: List[dict] = await self.LLMservice.get_models_list()
        result = [LlmResponseSchema.model_validate(key) for key in response]
        return result

    async def create(self, data: OllamaCreate, session: AsyncSession = Depends(get_db)) -> OllamaRead:
        return await super().create(data, session)

    async def patch(self, id: int, data: OllamaUpdate,
                    background_tasks: BackgroundTasks,
                    session: AsyncSession = Depends(get_db)) -> OllamaRead:
        return await super().patch(id, data, background_tasks, session)
