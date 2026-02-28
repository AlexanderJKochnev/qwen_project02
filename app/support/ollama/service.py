# app.suport.ollama.service.py
from app.support.ollama.repository import OllamaRepository


class OllamaService:
    def __init__(self):
        self.repository = OllamaRepository()

    async def get_models_list(self):
        result = await self.repository.get_models_list()
        return result