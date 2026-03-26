# app.support.vllm.service.py
import time
from typing import List

from loguru import logger
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.types import ModelType
from app.core.utils.benchmarks import get_metrics
from app.core.utils.common_utils import jprint
from app.support.ollama.model import ISOLanguage, Prompt, Proption, WriterRule
from app.support.ollama.repository import ISOLanguageRepository, PromptRepository, ProptionRepository, \
    WriterRuleRepository


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
            # base_url=settings.VLLM_URL,  # "http://localhost:8000/v1"),
            base_url='http://vllm-node:8000/v1/',
            api_key="token-not-needed"
        )
        self.model_name = "/model"  # "Qwen/Qwen2.5-7B-Instruct-GPTQ"

    async def get_datas(self, phrase: str, prompt: str, proption: str, writer: str, language: str,
                        session: AsyncSession):
        langs = [lang.strip() for lang in language.split(',')]
        lang_response: List[ISOLanguage] = await ISOLanguageRepository.search_by_list_value_exact(langs, 'iso_639_1', ISOLanguage,
                                                                                                  session)
        if lang_response:
            language_set = {lang.iso_639_1 for lang in lang_response}
        dataset = {'prompt': (Prompt, PromptRepository, 'role', 'system_prompt', prompt),
                   'writer': (WriterRule, WriterRuleRepository, 'name', 'prompt', writer),
                   'proption': (Proption, ProptionRepository, 'preset', None, proption)}
        payload: dict = {}
        for key, val in dataset.items():
            model, repo, field_name, field_out, search = val
            tmp: ModelType = await repo.get_by_field(field_name, search, model, session)
            if field_out:
                payload[key] = getattr(tmp, field_out)
            else:
                payload[key] = tmp.to_dict()
        result: dict = {}
        for lang in language_set:
            logger.warning(f'--------{lang}----------------')
            response = await self.performing(lang, phrase, payload)
            logger.warning(f'--------{type(response)=}----------------')
            jprint(response)
            result[lang] = response  # .choices[0].message.content
        return result

    async def performing(self, lang: str, phrase: str, payload: dict):
        """
            перевод/генерация
        """
        try:
            start_ms = time.time() * 1000
            options = payload.get("proption", {})
            gpu_ms = time.time() * 1000
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "system", "content": payload.get("prompt", "")},
                          # Маппинг ваших параметров в формат OpenAI/v)LM
                          {"role": "user", "content": payload.get("writer", "").format(lang=lang, phrase=phrase)}],
                temperature=options.get("temperature", 0.1), top_p=options.get("top_p", 0.1),
                max_tokens=options.get("num_predict", 1024), presence_penalty=options.get("presence_penalty", 0),
                frequency_penalty=options.get("frequency_penalty", 0), seed=options.get("seed", 42),
                stop=options.get("stop", None)
            )
            response = get_metrics(response.choices[0].message.content,
                                   response.usage.completion_tokens,
                                   start_ms, gpu_ms
                                   )
            return response
            # return response.choices[0].message.content
        except Exception as x:
            logger.error(f'base_url "http://172.60.0.10/v1", error: {x}')
            return {'result': False}

    async def get_translate(self, phrase, prompt: str, proption: str, writer: str, langs: str,
                            session: AsyncSession,
                            **kwargs):
        # phrase, prompt, preset, writer, langs, session
        result = await self.get_datas(phrase, prompt, proption, writer, langs, session)

        return {'response': True if result else False,
                'answer': result}
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": writer},
                {"role": "user", "content": prompt}
            ],
            **kwargs  # Передача температуры и других параметров
        )
        return response.choices[0].message.content
