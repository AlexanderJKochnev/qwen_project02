# app.core.utils.background_tasks.py
from functools import wraps
from typing import Callable
from loguru import logger


def background(func: Callable) -> Callable:
    """Декоратор для асинхронных методов, которые должны выполняться только в фоне
       @backround
       @classmethod
       def ...
       как вызвать из роутера
       async def process(background_tasks: BackgroundTasks):
            return await UserService.process_users(**kwargs,background_tasks=background_tasks)
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Извлекаем background_tasks (он обязательно должен быть в kwargs)
        background_tasks = kwargs.pop('background_tasks')

        background_tasks.add_task(func, *args, **kwargs)
        logger.success(f'function {func.__name__} added to background tasks')
        # в самом методе добавить в конце
        # logger.success('фоновая задача завершена')
        return {"status": "queued", "task": func.__name__}

    return wrapper
