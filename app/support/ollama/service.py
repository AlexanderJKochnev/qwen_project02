# app.suport.ollama.service.py
from loguru import logger
from fastapi import BackgroundTasks
from ollama import ListResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.service import Service
from app.core.types import ModelType
from app.support.ollama.repository import LLMRepository, OllamaRepository


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

    @classmethod
    async def maintain_llm_database(cls, data: dict,
                                    repository: OllamaRepository, model: ModelType,
                                    background_tasks: BackgroundTasks,
                                    session: AsyncSession):
        """
         1. получает словарь
            1.1. added: модели для бобавления
            1.2. removed: млдели для удаления
            1.3. changed: модели для изменения
         2. соотвественно обновляет/добавляет/удаляет
        """
        try:
            if added := data.get('added'):
                for key in added:
                    await cls.create(key, repository, model, session)
            if remove := data.get('remove'):
                for key in remove:
                    await cls.delete(key, model, repository, background_tasks, session)
            if changed := data.get('changed'):
                for key in changed:
                    await cls.update_or_create(key, repository, model, background_tasks, session)
        except Exception as e:
            logger.error(f'maintain_llm_database. {e}')
            raise Exception(e)
