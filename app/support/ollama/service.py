# app.suport.ollama.service.py
from typing import List, Tuple, Type, Dict

from ollama import ListResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.sqlalchemy_repository import Repository
from app.core.services.service import Service
from app.core.types import ModelType
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
    default = ['model']

    def maintain_llm_database(cls, data: dict, repository: OllamaRepository, model: ModelType, session: AsyncSession):
        """
         1. получает словарь
            1.1. added: модели для бобавления
            1.2. removed: млдели для удаления
            1.3. changed: модели для изменения
         2. соотвественно обновляет/добавляет/удаляет
        """
        pass