# app.suport.ollama.service.py
import asyncio

from loguru import logger
from ollama import ListResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Type
from app.core.services.service import Service
from app.core.types import ModelType
from app.core.utils.ollama_utils import build_ollama_payload
# from app.support.ollama.schemas import LlmResponseSchema
from app.support.ollama.repository import (LLMRepository, OllamaRepository, PromptRepository, Repository,
                                           ISOLanguageRepository, ProptionRepository, WriterRuleRepository)
from app.support.ollama.model import Ollama, ISOLanguage, Prompt, Proption, WriterRule


class LLMService:
    def __init__(self):
        # self.repository = OllamaRepository()
        self.LLMrepository = LLMRepository()

    async def get_models_list(self) -> List[dict]:
        result: ListResponse = await self.LLMrepository.get_models_list()
        tmp_dict: dict = result.model_dump()  # {'models': [{...}, список моделей описнаний]
        response: List[dict] = [a for a in tmp_dict.get('models')]
        return response

    async def del_model(self, model: str) -> bool:
        return await self.LLMrepository.del_model(model)


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
                    await repository.delete(key, session)
            if changed := data.get('changed'):
                for obj, data in changed:
                    await repository.patch(obj, data, session)
        except Exception as e:
            logger.error(f'maintain_llm_database. {e}')
            raise Exception(e)

    @classmethod
    async def get_datas(cls, search: str, repo: Type[Repository],
                        model: Type[ModelType], session: AsyncSession, **kwargs) -> ModelType:
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
                                    prompt_dict: dict, preset_dict: dict,
                                    writer: str,
                                    llm_repository: LLMRepository):
        """
            перевод на один язык
        """
        try:
            # source: str = f"Only translate the following text to {lang} '{phrase}'."
            kwargs = {'lang': lang, 'phrase': phrase}
            source: str = writer.format(**kwargs)
            prompt_dict.update(preset_dict)
            payload = build_ollama_payload(prompt_dict, source, llmodel, 'generate')
            # from app.core.utils.common_utils import jprint
            # jprint(payload)
            response = await llm_repository.get_translate(payload)
            total_duration_ns = response.get('total_duration')
            tmp: dict = {'lang': lang, 'response': response.get('response'),
                         'llmodel': llmodel,
                         'prompt': prompt_dict.get('role'),
                         'duration': f"{total_duration_ns / 1_000_000_000: .2f}"}
            return tmp
        except Exception as e:
            return {'lang': lang, 'error': e}

    @classmethod
    async def write_the_novel(cls, phrase: str, lang: str, llmodel: str,
                              prompt_dict: dict,
                              preset_dict: dict,
                              writer: str,
                              llm_repository: (
            LLMRepository)) -> dict:
        """ описание на одном языке """
        try:
            """source: str = (f'Напиши статью о "{phrase}" (3-4 предложения) на {lang} язык, '
                           f'Правила: смысловая точность перевода прежде всего, '
                           f'можно немного подумать про себя и сразу переходи к ответу, '
                           f'не анализируй запрос вслух, Пиши только финальный текст')"""
            kwargs = {'lang': lang, 'phrase': phrase}
            source: str = writer.format(**kwargs)
            prompt_dict.update(preset_dict)
            payload: dict = build_ollama_payload(prompt_dict, source, llmodel, 'generate')
            response = await llm_repository.get_translate(payload)
            total_duration_ns = response.get('total_duration')
            tmp: dict = {'source': phrase, 'response': response.get('response'),
                         'llmodel': llmodel,
                         'prompt': prompt_dict.get('role'),
                         'duration': f"{total_duration_ns / 1_000_000_000: .2f}"}
            return tmp
        except Exception as e:
            return {'llmodel': llmodel, 'prompt': prompt_dict, 'error': e}

    @classmethod
    async def write_the_novel_with_verification(
        cls, phrase: str, lang: str, llmodel: str, prompt_dict: dict, preset_dict: dict, writer: str,
        llm_repository: (LLMRepository)
    ) -> dict:
        """ описание на одном языке """
        try:
            kwargs = {'lang': lang, 'phrase': phrase}
            source: str = writer.format(**kwargs)
            prompt_dict.update(preset_dict)
            payload: dict = build_ollama_payload(prompt_dict, source, llmodel, 'generate')
            # from app.core.utils.common_utils import jprint
            # jprint(payload)
            response = await llm_repository.get_translate(payload)
            initial_text = response.get('response')
            duration: list = []
            duration.append(response.get('total_duration'))
            # 2. verification
            verification_prompt: str = (f"Твоя задача — проверить следующий текст "
                                        f"на наличие фактических ошибок. Текст для проверки: "
                                        f"{initial_text} "
                                        f"Проанализируй каждое утверждение и отметь ТОЛЬКО те, которые:"
                                        f"1. Содержат исторические факты (даты, имена, события) "
                                        f"2. Утверждают что-то о производителе или создателе "
                                        f"3. Содержат сравнительные характеристики с другими брендами "
                                        f"Для каждого сомнительного утверждения укажи:"
                                        f"- Цитату из текста "
                                        f"- Почему это может быть недостоверно "
                                        f"Если все факты достоверны, "
                                        f"ответь: 'ВСЕ ФАКТЫ ДОСТОВЕРНЫ'")
            payload['prompt'] = verification_prompt
            payload['system'] = "Ты — строгий факт-чекер. Проверяй каждое утверждение."
            payload['options']['temperature'] = 0.1
            verification_response = await llm_repository.get_translate(payload)
            verification_text = verification_response.get('response', '')
            duration.append(verification_response.get('total_duration'))
            if "ВСЕ ФАКТЫ ДОСТОВЕРНЫ" not in verification_text.upper():
                # 3. correction of initial text
                correction_prompt = (f"Перепиши следующий текст, ИСПРАВЛЯЯ или УДАЛЯЯ сомнительные утверждения."
                                     f"Оригинальный текст: {initial_text} "
                                     f"Результаты проверки (проблемные места): {verification_text} "
                                     f"Правила исправления:"
                                     f"1. Если факт сомнительный — удали его полностью "
                                     f"2. Если не уверен в дате или имени — убери конкретику "
                                     f"3. Сохрани общий стиль и описание вкуса/аромата "
                                     f"4. Не добавляй новых фактов сверх исходного текста "
                                     f"Исправленный текст: ")
                payload['prompt'] = correction_prompt
                payload['system'] = "Ты — редактор, удаляющий фактические ошибки."
                final_response = await llm_repository.get_translate(payload)
                final_text = final_response.get('response', initial_text)
                duration.append(final_response.get('total_duration'))
            else:
                final_text = initial_text
                verification_text = "Ошибок не найдено"
            total_duration = {f'duration of {n + 1} stage': f"{v / 1_000_000_000: .2f}" for n, v in enumerate(duration)}
            tmp: dict = {'source': phrase,
                         'llmodel': llmodel,
                         'prompt': prompt_dict.get('role'),
                         'initial_response': response.get('response'),
                         'verification_text': verification_text,
                         'final_text': final_text,
                         'total_duration': total_duration}
            return tmp
        except Exception as e:
            return {'llmodel': llmodel, 'prompt': prompt_dict, 'error': e}

    @classmethod
    async def get_translate(cls, phrase: str,
                            search_model: str,
                            search_prompt: str,
                            search_preset: str,
                            search_write: str,
                            langs: str,
                            session: AsyncSession):
        """ перевод на несколько  языков """
        try:
            llm_repository = LLMRepository()
            llmodel, prompt_dict, preset_dict, writer, languages = await cls.prepaire(search_model, search_prompt,
                                                                                      search_preset, search_write,
                                                                                      langs, session)
            # 5. подготовка к параллельному запуску:
            tasks = [cls.translate_to_language(phrase, lang, llmodel, prompt_dict, preset_dict, writer,
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

    @classmethod
    async def get_novel(cls, phrase: str,
                        search_model: str,
                        search_prompt: str,
                        search_preset: str,
                        search_write: str,
                        langs: str,
                        verify: bool,
                        session: AsyncSession) -> dict:
        """
        генерация описаний
        """
        try:
            llm_repository = LLMRepository()
            llmodel, prompt_dict, preset_dict, writer, languages = await cls.prepaire(
                search_model, search_prompt, search_preset, search_write, langs, session
            )
            language = languages[0]
            # 5. подготовка к параллельному запуску:
            tasks = [cls.write_the_novel(
                phrase, lang, llmodel, prompt_dict, preset_dict, writer, llm_repository
            ) for lang in languages]
            result = await asyncio.gather(*tasks)

            # all bellow are generation with verification. this is double long procedure therefore ii works for one
            # language per request
            language = languages[0]
            if not verify:
                result: dict = await cls.write_the_novel(phrase, language, llmodel, prompt_dict, preset_dict,
                                                         writer, llm_repository)
            else:
                result = await cls.write_the_novel_with_verification(
                    phrase, language, llmodel, prompt_dict, preset_dict, writer, llm_repository
                )
            return result

        except ValueError as e:
            # Обрабатываем ошибки валидации/поиска
            logger.error(f"Validation error: {e}")
            raise  # Пробрасываем дальше для обработки в роутере

        except Exception as e:
            # Обрабатываем непредвиденные ошибки
            logger.error(f"Unexpected error in get_novel: {e}", exc_info=True)
            raise RuntimeError(f"Internal server error during get_novel: {str(e)}")

    @classmethod
    async def prepaire(cls, search_model: str, search_prompt: str, search_preset: str,
                       search_write: str,
                       langs: str,  # 'ru,en,fr'
                       session: AsyncSession) -> tuple:
        """
        получение
        ll_model: str
        prompt: dict
        preset: dict
        writer:
        langs: list
        """
        # 1. Поиск и получение ll model
        response = await cls.get_datas(
            search_model, OllamaRepository, Ollama, session, order_by='size', asc=True, equa='icontains',
            field='model'
        )
        llmodel: str = response.model
        # 2. Поиск и получение prompt
        prompt: Prompt = await cls.get_datas(
            search_prompt, PromptRepository, Prompt, session, order_by='role', asc=True, equa='icontains',
            field='role'
        )
        prompt_dict = prompt.to_dict()
        # 3. Поиск и получение preset
        preset: Proption = await cls.get_datas(
            search_preset, ProptionRepository, Proption, session, order_by='preset', asc=True, equa='icontains',
            field='preset'
        )
        preset_dict = preset.to_dict()
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
        languages: str = [val.name_en for val in result]
        logger.warning(f'{languages=}')
        # 4. получение writer
        wrt: WriterRule = await cls.get_datas(
            search_write, WriterRuleRepository, WriterRule, session, order_by='name', asc=True,
            equa='icontains', field='name'
        )
        writer: str = wrt.prompt
        return llmodel, prompt_dict, preset_dict, writer, languages


class PromptService(Service):
    default = ['role']


class ProptionService(Service):
    default = ['preset']


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


class WriterRuleService(Service):
    default = ['name']
