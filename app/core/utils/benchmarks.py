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


def get_metrics(content: str, completion_tokens: int, start_ms: float, gpu_start_ms: float) -> dict:
    now_ms = time.time() * 1000
    total_ms = now_ms - start_ms
    gpu_ms = now_ms - gpu_start_ms
    speed = round(completion_tokens / (gpu_ms / 1000), 1) if gpu_ms > 0 else 0

    return {'content': f"{content}\n\n---\n{round(total_ms, 1)}ms | {completion_tokens} tok | {speed} tok/s",
            'performance': {'total_ms': round(total_ms, 1), 'gpu_ms': round(gpu_ms, 1), 'tokens': completion_tokens,
                            'speed_tok_per_sec': speed}}
