# app.suport.ollama.service.py
from loguru import logger
from ollama import ListResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.services.service import Service
from app.core.types import ModelType
from app.support.ollama.schemas import LlmResponseSchema
from app.support.ollama.repository import LLMRepository, OllamaRepository, PromptRepository
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
    async def get_translate(cls, phrase: str,
                            search_model: str,
                            prompt: str,
                            langs: str,
                            session: AsyncSession):
        """ поиск """
        # 1. Поиск и получение ll model
        repo = OllamaRepository
        model = Ollama
        if search_model.isnumeric():
            response: Ollama = await repo.get_by_id(int(search_model), model, session)
        else:
            response: Ollama = await repo.get_by_field('model', search_model, model, session)
        llmodel = response.model
        logger.warning(llmodel)

        # 2. Поиск и получение prompt
        # 3. получение списка языков
        # 4. формирование payload (build_ollama_payload)
        # 5. запуск перевода (asyncio.gather)
        return None


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
