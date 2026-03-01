# app.suport.ollama.service.py
from ollama import ListResponse
from app.core.services.service import Service
from app.support.ollama.repository import OllamaRepository, LLMRepository


class LLMService:
    def __init__(self):
        # self.repository = OllamaRepository()
        self.LLMrepository = LLMRepository()

    async def get_models_list(self):
        result: ListResponse = await self.LLMrepository.get_models_list()
        tmp = result.model_dump()
        return tmp.get('models')


class OllamaService(Service):
    pass
