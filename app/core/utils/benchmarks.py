# Benchmark проверки IP
import time


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

    return {'content': content,
            'performance': {'total_sec': round(total_ms / 1000, 3),
                            'gpu_s': round(gpu_ms, 1),
                            'tokens': completion_tokens,
                            'speed_tok_per_sec': speed}}
