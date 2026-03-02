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

    def create_or_update(cls, data: Dict, repository: Type[Repository],
                         model: ModelType, session: AsyncSession,
                         default: List[str] = None, **kwargs) -> Tuple[ModelType, bool]:
        """
         1. ищет запись, если найдена:
         2. обновляе, если нет:
         3. создает
         data: данные для обновления
         default: список полей по которым осуществляется поиск существуюих запсией
        """
        