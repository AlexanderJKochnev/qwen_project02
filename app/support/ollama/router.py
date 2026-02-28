# app.suport.ollama.router.py
from app.core.routers.base import LightRouter
from app.support.ollama.service import OllamaService


class OllamaRouter(LightRouter):
    def __init__(self):
        super().__init__(
            prefix="/ollama",
        )
        self.service = OllamaService()

    def setup_routes(self):
        self.router.add_api_route("", self.endpoints,
                                  methods=["GET"],
                                  response_model=dict)

    def get_models_list(self):
        """
        получение загруженных моделей
        """
        response = self.service.get_models_list()
        return response