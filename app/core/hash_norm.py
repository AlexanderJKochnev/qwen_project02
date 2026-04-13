# app.core.hash_norm.py
"""  нормализация текста для хэширования """
import string
from loguru import logger
import struct
from functools import lru_cache
from typing import List

import cityhash

# --- КОНФИГУРАЦИЯ И НОРМАЛИЗАЦИЯ ---

_EXTRA_FIXES = {
    'ü': 'u', 'ö': 'o', 'ä': 'a', 'ß': 'ss', 'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
    'à': 'a', 'â': 'a', 'î': 'i', 'ï': 'i', 'ô': 'o', 'û': 'u', 'ù': 'u', 'ç': 'c',
    'ñ': 'n', 'á': 'a', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ã': 'a', 'õ': 'o', 'å': 'a',
    'ø': 'o', 'æ': 'ae', 'ł': 'l', 'ń': 'n', 'ś': 's', 'ź': 'z', 'ż': 'z',
    '.': '#', ',': '#'
}

_ALLOWED = string.ascii_lowercase + string.digits + "абвгдёежзийклмнопрстуфхцчшщъыьэюя#"
_TRANS_MAP = str.maketrans({
    **{chr(i): ' ' for i in range(65536)},
    **{c: c for c in _ALLOWED},
    **_EXTRA_FIXES
})


@lru_cache(maxsize=65536)
def get_cached_hash(token: str) -> int:
    """Детерминированный CityHash64 -> Signed BigInt."""
    h_unsigned = cityhash.CityHash64(token)
    return struct.unpack('q', struct.pack('Q', h_unsigned))[0]


def is_valid_token(t: str) -> bool:
    """Фильтрация: длина > 1 и числа только в диапазоне 1-2050."""
    if not t or len(t) < 2:
        return False
    clean_t = t.replace('#', '')
    if clean_t.isdigit():
        try:
            val = int(t.split('#')[0])
            return 1 <= val <= 2050
        except Exception as e:
            logger.error(f' is_valid_token. {e}')
            return False
    return True


def tokenize(text: str) -> List[str]:
    """Превращает сырой текст в список чистых слов (с сохранением повторов)."""
    if not text:
        return []
    return [
        t for t in (w.strip('#') for w in text.lower().translate(_TRANS_MAP).split())
        if is_valid_token(t)
    ]

# --- ФУНКЦИИ ДЛЯ ПОДДЕРЖКИ БАЗЫ ---


def get_hashes_for_item(text: str) -> List[int]:
    """
    Генерирует уникальные хеши для поля word_hashes (для GIN индекса).
    Использовать в макросе обновления айтема.
    """
    # set() здесь уместен, т.к. для GIN индекса дубликаты вредны
    return [get_cached_hash(t) for t in set(tokenize(text))]
