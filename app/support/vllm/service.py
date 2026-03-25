# app.support.vllm.service.py
from openai import AsyncOpenAI
from typing import List
from loguru import logger
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

    async def get_datas(self, prompt: int, proption: str, writer: str, language: str, session: AsyncSession):
        from app.core.utils.common_utils import jprint
        langs = [lang.strip() for lang in language.split(',')]
        lang_response: List[ISOLanguage] = await ISOLanguageRepository.search_by_list_value_exact(langs, 'iso_639_1', ISOLanguage,
                                                                                                  session)
        logger.warning('-----------4----------------')

        if lang_response:
            language_set = {lang.iso_639_1 for lang in lang_response}
            logger.warning(f'{language_set=}')
        dataset = {'prompt': (Prompt, PromptRepository, 'role', 'system_prompt', prompt),
                   'writer': (WriterRule, WriterRuleRepository, 'name', 'prompt', writer),
                   'proption': (Proption, ProptionRepository, 'preset', None, proption)}
        response: dict = {}
        print('======================================================')
        for key, val in dataset.items():
            model, repo, field_name, field_out, search = val
            tmp = await repo.get_by_field(field_name, search, model, session)
            logger.warning(f'{search=}, {field_out=}')
            response[key] = getattr(tmp, field_out)
        response['langs'] = language_set
        return response

    async def get_translate(self, phrase, prompt: str, proption: str, writer: str, langs: str,
                            session: AsyncSession,
                            **kwargs):
        # phrase, prompt, preset, writer, langs, session
        logger.warning('-----------1----------------')
        result = await self.get_datas(prompt, proption, writer, langs, session)
        return result
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": writer},
                {"role": "user", "content": prompt}
            ],
            **kwargs  # Передача температуры и других параметров
        )
        return response.choices[0].message.content
