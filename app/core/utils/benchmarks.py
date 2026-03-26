# Benchmark проверки IP
import time
import functools
from loguru import logger
# import json
from typing import Dict, Any, Callable, Awaitable, Optional
from datetime import datetime


def check_ip_speed(host):
    start = time.time()
    internal_prefixes = ["127.0.0.1", "172.", "192.168.", "10.", "frontend"]
    for prefix in internal_prefixes:
        if host.startswith(prefix):
            break
    return time.time() - start


def add_performance_metrics(
        vllm_response: Dict[str, Any], start_time: float, gpu_start_time: Optional[float] = None
) -> Dict[str, Any]:
    """
    Добавляет метрики производительности к ответу vLLM.

    Args:
        vllm_response: Ответ от vLLM API
        start_time: Время начала всего запроса (включая обвязку)
        gpu_start_time: Время отправки запроса к vLLM (исключает обвязку)

    Returns:
        Обогащенный ответ с метриками
    """
    # Копируем ответ, чтобы не изменять оригинал
    enriched_response = vllm_response.copy()

    # Получаем текущее время
    now = time.time()

    # Общее время выполнения (включая обвязку)
    total_elapsed = now - start_time

    # Время работы GPU (только vLLM обработка)
    gpu_elapsed = None
    if gpu_start_time:
        gpu_elapsed = now - gpu_start_time

    # Получаем количество токенов из usage
    usage = vllm_response.get('usage', {})
    prompt_tokens = usage.get('prompt_tokens', 0)
    completion_tokens = usage.get('completion_tokens', 0)
    total_tokens = usage.get('total_tokens', 0)

    # Рассчитываем скорости
    speeds = {}
    if total_elapsed > 0:
        speeds['total_tokens_per_sec'] = round(total_tokens / total_elapsed, 2)
        if completion_tokens > 0:
            speeds['generation_tokens_per_sec'] = round(completion_tokens / total_elapsed, 2)

    if gpu_elapsed and gpu_elapsed > 0:
        speeds['gpu_tokens_per_sec'] = round(total_tokens / gpu_elapsed, 2)
        speeds['gpu_generation_tokens_per_sec'] = round(completion_tokens / gpu_elapsed, 2)

    # Добавляем метрики в ответ
    enriched_response['performance'] = {'timing': {'total_elapsed_seconds': round(total_elapsed, 3),
                                                   'gpu_elapsed_seconds': round(gpu_elapsed, 3) if gpu_elapsed else None,
                                                   'overhead_seconds': round(total_elapsed - (gpu_elapsed or total_elapsed), 3)},
                                        'tokens': {'prompt': prompt_tokens, 'completion': completion_tokens, 'total': total_tokens},
                                        'speed': speeds}

    # Добавляем метрики в content (опционально)
    if enriched_response.get('choices'):
        original_content = enriched_response['choices'][0]['message']['content']

        # Форматируем метрики для отображения
        metrics_text = "\n\n---\n**Performance Metrics:**\n"
        metrics_text += f"- Total time: {round(total_elapsed, 2)}s\n"

        if gpu_elapsed:
            metrics_text += f"- GPU time: {round(gpu_elapsed, 2)}s\n"
            metrics_text += f"- Overhead: {round(total_elapsed - gpu_elapsed, 2)}s\n"

        metrics_text += f"- Tokens: {completion_tokens} generated, {total_tokens} total\n"
        metrics_text += f"- Speed: {speeds.get('generation_tokens_per_sec', 0)} tokens/s (gen)"

        if gpu_elapsed:
            metrics_text += f", {speeds.get('gpu_generation_tokens_per_sec', 0)} tokens/s (GPU gen)"

        # Добавляем метрики в конец сообщения
        enriched_response['choices'][0]['message']['content'] = original_content + metrics_text

    return enriched_response


def with_vllm_metrics(include_in_content: bool = True):
    """
    Декоратор для обогащения ответа vLLM метриками производительности.
    """

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Dict[str, Any]]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Dict[str, Any]:
            total_start_ms = time.time() * 1000
            gpu_start_ms = time.time() * 1000
            logger.warning('==i"am in wrapper')
            # Вызываем оригинальную функцию, получаем Pydantic объект
            vllm_response = await func(*args, **kwargs)
            logger.warning("after vlimm")

            gpu_end_ms = time.time() * 1000
            total_end_ms = time.time() * 1000

            # Извлекаем данные через атрибуты
            content = vllm_response.choices[0].message.content
            completion_tokens = vllm_response.usage.completion_tokens

            # Время
            gpu_elapsed_ms = gpu_end_ms - gpu_start_ms
            total_elapsed_ms = total_end_ms - total_start_ms

            # Скорость
            speed = round(completion_tokens / (gpu_elapsed_ms / 1000), 1) if gpu_elapsed_ms > 0 else 0

            # Формируем результат
            output = {'content': content,
                      'performance': {'time_ms': round(total_elapsed_ms, 1), 'gpu_time_ms': round(gpu_elapsed_ms, 1),
                                      'tokens': completion_tokens, 'speed_tok_per_sec': speed}}

            # Добавляем метрики в текст
            if include_in_content and content:
                output['content'] = (f"{content}\n\n"
                                     f"---\n"
                                     f"{round(total_elapsed_ms, 1)}ms | "
                                     f"{completion_tokens} tok | "
                                     f"{speed} tok/s")

            return output

        return wrapper

    return decorator
