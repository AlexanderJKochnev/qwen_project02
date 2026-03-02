# app.suport.ollama.router.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request, BackgroundTasks
from app.core.routers.base import LightRouter, BaseRouter
from app.support.ollama.service import OllamaService, LLMService
from app.support.ollama.schemas import LlmResponseSchema, OllamaCreate, OllamaUpdate, OllamaRead
from app.support.ollama.model import Ollama


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

    async def create(self, data: OllamaCreate) -> OllamaRead:
        return await super().create(data)

    async def patch(self, id: int, data: OllamaUpdate, background_tasks: BackgroundTasks) -> OllamaRead:
        return await super().patch(id, data, background_tasks)
