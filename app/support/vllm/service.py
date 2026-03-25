# app.support.vllm.service.py
from openai import AsyncOpenAI
import os
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.repositories.sqlalchemy_repository import Repository
from app.core.types import ModelType
from app.support.ollama.model import Prompt, WriterRule, ISOLanguage, Proption
from app.support.ollama.repository import PromptRepository, WriterRuleRepository, ISOLanguageRepository, ProptionRepository


class VLLMService:
    """
    1. получение даннных
    2. загрузка: prompt, preset, langs, proption
    3. подготовка запроса
    4. запрос/ответ
    5. encoding
    """
    def __init__(self):
        # vLLM по умолчанию работает на http://localhost:8000/v1
        self.client = AsyncOpenAI(
            base_url=os.getenv("VLLM_URL", "http://localhost:8000/v1"),
            api_key="token-not-needed"
        )
        self.model_name = "Qwen/Qwen2.5-7B-Instruct-AWQ"

    async def get_datas(self, prompt: int, preset: int, proption: str, language: str, session: AsyncSession):
        langs = (lang.strip() for lang in language.split(','))
        lang_set = await ISOLanguageRepository.search_by_list_value_exact(langs, 'iso_639_1', ISOLanguage, session)

        dataset = {'prompt': (Prompt, PromptRepository, 'role', 'system_prompt', prompt),
                   'writer': (WriterRule, WriterRuleRepository, 'name', 'prompt', preset),
                   'proption': (Proption, ProptionRepository, 'preset', None)}

    async def get_datas1(self, search: str, field: str, model: ModelType, repository: Repository):
        return await repository.get_by_fields()

    async def get_translate(self, phrase, prompt: str, preset: str, writer: str, langs: str,
                            session: AsyncSession,
                            **kwargs):
        # phrase, prompt, preset, writer, langs, session
        return {'result': True}
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": writer},
                {"role": "user", "content": prompt}
            ],
            **kwargs  # Передача температуры и других параметров
        )
        return response.choices[0].message.content
