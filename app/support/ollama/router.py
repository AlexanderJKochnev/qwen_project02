# app.suport.ollama.router.py
from typing import List
from app.core.routers.base import LightRouter
from app.support.ollama.service import OllamaService
from app.support.ollama.schemas import LLModels


class OllamaRouter(LightRouter):
    def __init__(self):
        super().__init__(
            prefix="/ollama",
        )
        self.service = OllamaService()

    def setup_routes(self):
        self.router.add_api_route("", self.get_models_list,
                                  methods=["GET"],
                                  response_model=List[LLModels])

    async def get_models_list(self):
        """
        получение загруженных моделей
        """
        response: List[dict] = await self.service.get_models_list()
        result = [LLModels.model_validate(key) for key in response]
        return result
