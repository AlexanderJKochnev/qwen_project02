# app.suport.ollama.router.py
from typing import List
from app.core.routers.base import LightRouter
from app.support.ollama.service import OllamaService, LLMService
from app.support.ollama.schemas import LlmResponseSchema
from app.support.ollama.model import Ollama


class OllamaRouter(LightRouter):
    def __init__(self):
        super().__init__(model=Ollama, prefix="/ollama")
        self.service = OllamaService
        self.LLMservice = LLMService()

    def setup_routes(self):
        self.router.add_api_route("", self.get_models_list,
                                  methods=["GET"],
                                  response_model=List[LlmResponseSchema])

    async def get_models_list(self):
        """
        получение загруженных моделей
        """
        response: List[dict] = await self.LLMservice.get_models_list()
        result = [LlmResponseSchema.model_validate(key) for key in response]
        return result
