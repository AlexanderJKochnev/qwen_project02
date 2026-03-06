# app.suport.ollama.service.py
import asyncio

from loguru import logger
from ollama import ListResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Type
from app.core.services.service import Service
from app.core.types import ModelType
from app.core.utils.ollama_utils import build_ollama_payload
from app.support.ollama.schemas import LlmResponseSchema
from app.support.ollama.repository import (LLMRepository, OllamaRepository, PromptRepository, Repository,
                                           ISOLanguageRepository)
from app.support.ollama.model import Ollama, ISOLanguage, Prompt


class LLMService:
    def __init__(self):
        # self.repository = OllamaRepository()
        self.LLMrepository = LLMRepository()

    async def get_models_list(self) -> List[dict]:
        result: ListResponse = await self.LLMrepository.get_models_list()
        tmp_dict: dict = result.model_dump()  # {'models': [{...}, список моделей описнаний]
        response: List[dict] = [a for a in tmp_dict.get('models')]
        return response


class OllamaService(Service):
    default = ['model']

    @classmethod
    async def maintain_llm_database(cls, data: dict,
                                    repository: OllamaRepository, model: ModelType,
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
                    await repository.create(model(**key), model, session)
            if remove := data.get('removed'):
                for key in remove:
                    result = await repository.delete(key, session)
                    logger.warning(f'{result=}, {key=}')
            if changed := data.get('changed'):
                for obj, data in changed:
                    await repository.patch(obj, data, session)
        except Exception as e:
            logger.error(f'maintain_llm_database. {e}')
            raise Exception(e)

    @classmethod
    async def get_datas(cls, search: str, repo: Type[Repository], model: ModelType, session: AsyncSession, **kwargs):
        """
            получение данных из базы данных (модель, prompt)
            сделать кэширование
        """
        if search.isnumeric():
            response: ModelType = await repo.get_by_id(int(search), model, session)
        else:
            field = kwargs.get('field', 'name')
            response: ModelType = await repo.get_by_field(
                field, search, model, session, **kwargs)
            # order_by='size', asc=True, equa='icontains'
        if not response:
            raise ValueError(f'LLM model "{search}" not found')
        return response

    @classmethod
    async def translate_to_language(cls, phrase: str, lang: str, llmodel: str,
                                    prompt_dict: dict, llm_repository: LLMRepository):
        """
            перевод на один язык
        """
        try:
            source: str = f"Only translate the following text to {lang} '{phrase}'."
            payload = build_ollama_payload(prompt_dict, source, llmodel, 'generate')
            response = await llm_repository.get_translate(payload)
            total_duration_ns = response.get('total_duration')
            tmp: dict = {'lang': lang, 'response': response.get('response'),
                         'llmodel': llmodel,
                         'duration': f"{total_duration_ns / 1_000_000_000: .2f}"}
            return tmp
        except Exception as e:
            return {'lang': lang, 'error': e}

    @classmethod
    async def write_the_novel(cls, phrase: str, llmodel: str, prompt_dict: dict, llm_repository: LLMRepository):
        """ описание на одном языке """
        try:
            source: str = f'Write a 3-4 sentence article about {phrase} in the style of The Oxford Companion to Wine'
            payload: dict = build_ollama_payload(prompt_dict, source, llmodel, 'generate')
            response = await llm_repository.get_translate(payload)
            total_duration_ns = response.get('total_duration')
            tmp: dict = {'source': phrase, 'response': response.get('response'),
                         'llmodel': llmodel,
                         'duration': f"{total_duration_ns / 1_000_000_000: .2f}"}
        except Exception as e:
            return {'llmodel': llmodel, 'prompt': prompt_dict, 'error': e}

    @classmethod
    async def get_translate(cls, phrase: str,
                            search_model: str,
                            search_prompt: str,
                            langs: str,
                            session: AsyncSession):
        """ перевод на несколько  языков """
        try:
            llm_repository = LLMRepository()
            # 1. Поиск и получение ll model
            response = await cls.get_datas(search_model, OllamaRepository, Ollama, session,
                                           order_by='size', asc=True, equa='icontains',
                                           field='model')
            llmodel: str = response.model

            # 2. Поиск и получение prompt
            prompt: Prompt = await cls.get_datas(search_prompt, PromptRepository, Prompt, session,
                                                 order_by='role', asc=True, equa='icontains',
                                                 field='role')
            prompt_dict = prompt.to_dict()
            # 3. получение списка языков
            if langs and isinstance(langs, str):
                iso = [lang.strip() for lang in langs.split(',')]
            else:
                iso = ['ru', 'en', 'zh']
            # определяем 3 или 2 знака
            match len(iso[0]):
                case 2:
                    conditions = {'iso_639_1': iso}
                case 3:
                    conditions = {'iso_639_3': iso}
                case _:
                    conditions = {'name_en': iso}
            repo = ISOLanguageRepository
            result: List[ISOLanguage] = await repo.search_by_conditions(conditions, ISOLanguage, session)
            languages = [val.name_en for val in result]
            # 4. подготовка к параллельному запуску:
            tasks = [cls.translate_to_language(phrase, lang, llmodel, prompt_dict,
                                               llm_repository) for lang in languages]
            result = await asyncio.gather(*tasks)
            return result
            return result
        except ValueError as e:
            # Обрабатываем ошибки валидации/поиска
            logger.error(f"Validation error: {e}")
            raise  # Пробрасываем дальше для обработки в роутере

        except Exception as e:
            # Обрабатываем непредвиденные ошибки
            logger.error(f"Unexpected error in get_translate: {e}", exc_info=True)
            raise RuntimeError(f"Internal server error during translation setup: {str(e)}")

    @classmethod
    async def get_novel(cls, phrase: str,
                        search_model: str,
                        search_prompt: str,
                        langs: str,
                        session: AsyncSession):
        """
        генерация описаний
        """
        try:
            llm_repository = LLMRepository()
            # 1. Поиск и получение ll model
            response = await cls.get_datas(search_model, OllamaRepository, Ollama, session,
                                           order_by='size', asc=True, equa='icontains',
                                           field='model')
            llmodel: str = response.model

            # 2. Поиск и получение prompt
            prompt: Prompt = await cls.get_datas(search_prompt, PromptRepository, Prompt, session,
                                                 order_by='role', asc=True, equa='icontains',
                                                 field='role')
            prompt_dict = prompt.to_dict()
            # 3. получение списка языков НЕ НУЖНО
            tasks = [cls.write_the_novel(phrase, llmodel, prompt_dict, llm_repository)]
            result = await asyncio.gather(*tasks)
            return result
            if langs and isinstance(langs, str):
                iso = [lang.strip() for lang in langs.split(',')]
            else:
                iso = ['ru', 'en', 'zh']
            # определяем 3 или 2 знака
            match len(iso[0]):
                case 2:
                    conditions = {'iso_639_1': iso}
                case 3:
                    conditions = {'iso_639_3': iso}
                case _:
                    conditions = {'name_en': iso}
            repo = ISOLanguageRepository
            result: List[ISOLanguage] = await repo.search_by_conditions(conditions, ISOLanguage, session)
            languages = [val.name_en for val in result]
            # 4. подготовка к параллельному запуску: НЕ НУЖНО
            tasks = [cls.translate_to_language(phrase, lang, llmodel, prompt_dict,
                                               llm_repository) for lang in languages]
            result = await asyncio.gather(*tasks)
            return result
        except ValueError as e:
            # Обрабатываем ошибки валидации/поиска
            logger.error(f"Validation error: {e}")
            raise  # Пробрасываем дальше для обработки в роутере

        except Exception as e:
            # Обрабатываем непредвиденные ошибки
            logger.error(f"Unexpected error in get_translate: {e}", exc_info=True)
            raise RuntimeError(f"Internal server error during translation setup: {str(e)}")


class PromptService(Service):
    default = ['role']


"""
    # Для метода GENERATE
    payload = OllamaRequestSchema.create_generate_payload(db_settings, user_task)

    response = await client.generate(
        model=payload.model,
        prompt=payload.prompt,
        system=payload.system,
        options=payload.options.model_dump(exclude_none=True),
        stream=payload.stream
    )

    # Для метода CHAT
    payload = OllamaRequestSchema.create_chat_payload(db_settings, user_task)

    response = await client.chat(
        model=payload.model,
        messages=payload.messages,
        options=payload.options.model_dump(exclude_none=True),
        stream=payload.stream
    )
    context только для generate
    async def translate_document(segments: list, db_settings):
    client = AsyncClient()
    current_context = None # В начале контекста нет

    for segment in segments:
        # 1. Формируем запрос, передавая накопленный контекст
        payload = OllamaRequestSchema.create_generate_payload(
            db_settings,
            segment,
            prev_context=current_context
        )

        # 2. Делаем запрос к Ollama
        response = await client.generate(
            model=payload.model,
            prompt=payload.prompt,
            system=payload.system,
            context=payload.context, # <--- ПЕРЕДАЕМ
            options=payload.options.model_dump(exclude_none=True)
        )

        # 3. Сохраняем НОВЫЙ контекст для следующего шага
        current_context = response.get('context')

        print(f"Перевод: {response['response']}")

"""


class ISOLanguageService(Service):
    default = ['iso_639_3']
