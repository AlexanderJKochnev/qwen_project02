# app.suport.ollama.service.py
from ollama import ListResponse
from app.support.ollama.repository import OllamaRepository


class OllamaService:
    def __init__(self):
        self.repository = OllamaRepository()

    async def get_models_list(self):
        result: ListResponse = await self.repository.get_models_list()
        tmp = result.model_dump()
        return tmp.get('models')
