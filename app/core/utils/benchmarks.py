# Benchmark проверки IP
import time
import functools
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


def with_vllm_metrics(enrich_content: bool = True):
    """
    Декоратор для обогащения ответа vLLM метриками производительности.

    Args:
        enrich_content: Добавлять ли метрики в content сообщения
    """

    def decorator(func: Callable[..., Awaitable[Dict[str, Any]]]) -> Callable[..., Awaitable[Dict[str, Any]]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Dict[str, Any]:
            # Засекаем время начала всего запроса
            total_start_ms = time.time() * 1000

            # Засекаем время перед вызовом vLLM (исключаем обвязку)
            gpu_start_ms = time.time() * 1000

            try:
                # Вызываем оригинальный метод (он должен вернуть ответ от vLLM)
                vllm_response = await func(*args, **kwargs)

                # Засекаем время получения ответа от vLLM
                gpu_end_ms = time.time() * 1000
                total_end_ms = gpu_end_ms

                # Рассчитываем время выполнения
                gpu_elapsed_ms = gpu_end_ms - gpu_start_ms
                total_elapsed_ms = total_end_ms - total_start_ms
                overhead_ms = total_elapsed_ms - gpu_elapsed_ms

                # Получаем количество токенов из usage
                usage = vllm_response.get('usage', {})
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)

                # Рассчитываем скорости (токенов в секунду)
                speeds = {}
                if total_elapsed_ms > 0:
                    total_elapsed_sec = total_elapsed_ms / 1000
                    speeds['total_tokens_per_sec'] = round(total_tokens / total_elapsed_sec, 2)
                    if completion_tokens > 0:
                        speeds['generation_tokens_per_sec'] = round(completion_tokens / total_elapsed_sec, 2)

                if gpu_elapsed_ms > 0:
                    gpu_elapsed_sec = gpu_elapsed_ms / 1000
                    speeds['gpu_tokens_per_sec'] = round(total_tokens / gpu_elapsed_sec, 2)
                    if completion_tokens > 0:
                        speeds['gpu_generation_tokens_per_sec'] = round(completion_tokens / gpu_elapsed_sec, 2)

                # Создаем объект с метриками
                metrics = {'timestamp': datetime.now().isoformat(),
                           'timing': {'total_elapsed_ms': round(total_elapsed_ms, 2),
                                      'gpu_elapsed_ms': round(gpu_elapsed_ms, 2), 'overhead_ms': round(overhead_ms, 2)},
                           'tokens': {'prompt': prompt_tokens, 'completion': completion_tokens, 'total': total_tokens},
                           'speed': speeds}

                # Обогащаем ответ метриками
                enriched_response = vllm_response.copy()
                enriched_response['performance'] = metrics

                # Если нужно, добавляем метрики в content
                if enrich_content and enriched_response.get('choices'):
                    # Форматируем метрики для отображения
                    metrics_text = (f"\n\n---\n"
                                    f"**⚡ Performance Metrics:**\n"
                                    f"• Total time: {round(total_elapsed_ms, 1)} ms\n"
                                    f"• GPU time: {round(gpu_elapsed_ms, 1)} ms\n"
                                    f"• Overhead: {round(overhead_ms, 1)} ms\n"
                                    f"• Tokens: {completion_tokens} generated, {total_tokens} total\n"
                                    f"• Speed: {speeds.get('generation_tokens_per_sec', 0)} tok/s (total)")

                    if speeds.get('gpu_generation_tokens_per_sec'):
                        metrics_text += f", {speeds.get('gpu_generation_tokens_per_sec')} tok/s (GPU)"

                    original_content = enriched_response['choices'][0]['message']['content']
                    enriched_response['choices'][0]['message']['content'] = original_content + metrics_text

                return enriched_response

            except Exception as e:
                # В случае ошибки, возвращаем метрики с информацией об ошибке
                total_end_ms = time.time() * 1000
                error_metrics = {'timestamp': datetime.now().isoformat(), 'error': str(e),
                                 'timing': {'total_elapsed_ms': round(total_end_ms - total_start_ms, 2), 'gpu_elapsed_ms': None,
                                            'overhead_ms': None}}

                if hasattr(e, 'response'):
                    return {'error': str(e), 'performance': error_metrics,
                            'original_response': getattr(e, 'response', None)}
                raise

        return wrapper

    return decorator
