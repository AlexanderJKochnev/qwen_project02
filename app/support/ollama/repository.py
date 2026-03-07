# app.suport.ollama.repository.py
from ollama import ListResponse, GenerateResponse
# from fastapi import Request
# from app.core.config.database.ollama_async import OllamaClientManager
from app.core.config.project_config import settings
from app.core.config.database.ollama_async import get_ollama_manager
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.ollama.model import Ollama, Prompt, ISOLanguage, Proption


class LLMRepository:
    def __init__(self):
        self.host = settings.OLLAMA_HOST
        self.ollama_manager = get_ollama_manager()
        # self.client = AsyncClient(host=self.host)

    async def get_models_list(self) -> ListResponse:
        """ получение списка моделей """
        models_info: ListResponse = await self.ollama_manager.client.list()
        return models_info

    async def del_model(self, model: str):
        return await self.ollama_manager.delete_model(model)

    async def get_translate(self, payload: dict):
        """  перевод
        response:
        {
            "model": "gemma2:27b",
            "created_at": "2026-03-05T09:02:43.415959219Z",
            "done": true,
            "done_reason": "stop",
            "total_duration": 1349323407,
            "load_duration": 379073222,
            "prompt_eval_count": 101,
            "prompt_eval_duration": 165122747,
            "eval_count": 6,
            "eval_duration": 796122539,
            "response": "Big White Lake \n",
            "thinking": null,
            "context": [
              106,
              1645,
              108,
              64748,
            ],
            "logprobs": null
          }

        """
        result: GenerateResponse = await self.ollama_manager.generate(**payload)
        from loguru import logger
        from app.core.utils.common_utils import jprint
        logger.warning(type(result))
        result_dict = result.model_dump()
        result_dict.pop('context')
        jprint(result_dict)
        logger.warning(result_dict.keys())
        return result

    async def check_and_pull(self):
        """Проверяет, есть ли модель, и скачивает её, если нет."""
        print(f"--- Проверка модели {self.model_name} ---")
        models_info = await self.client.list()

        # Проверяем наличие модели в списке установленных
        installed_models = [m['name'] for m in models_info['models']]

        if any(self.model_name in m for m in installed_models):
            print(f"Модель {self.model_name} уже готова к работе.")
        else:
            print("Модель не найдена. Начинаю скачивание...")
            # stream=True позволяет видеть прогресс скачивания
            async for progress in await self.client.pull(self.model_name, stream=True):
                status = progress.get('status', '')
                completed = progress.get('completed', 0)
                total = progress.get('total', 1)
                percent = (completed / total) * 100 if total > 0 else 0
                print(f"\rСтатус: {status} | Прогресс: {percent:.1f}%", end="")
            print("\nЗагрузка завершена!")

    async def ask(self, prompt: str, system_prompt: str = "Ты — полезный помощник."):
        """Отправляет запрос и возвращает полный ответ."""
        try:
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': prompt}]
            response = await self.client.chat(model=self.model_name, messages=messages)
            return response['message']['content']
        except Exception as e:
            return f"Ошибка при запросе: {e}"

    async def ask_stream(self, prompt: str):
        """Потоковая генерация (стриминг) для мгновенного вывода."""
        messages = [{'role': 'user', 'content': prompt}]
        async for part in await self.client.chat(model=self.model_name, messages=messages, stream=True):
            content = part['message']['content']
            yield content


class OllamaRepository(Repository):
    model = Ollama


class PromptRepository(Repository):
    model = Prompt


class ProptionRepository(Repository):
    model = Proption


class ISOLanguageRepository(Repository):
    model = ISOLanguage
