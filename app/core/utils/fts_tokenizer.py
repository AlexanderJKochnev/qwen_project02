# app.core.utils.fts_tokenizer.py
import string
from typing import Tuple

from loguru import logger


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


def tokenizer(text: str, ) -> Tuple[str] | None:
    """Превращает сырой текст в список чистых слов (удаляет/сохраняет сохранением повторов)."""
    if not text:
        return None
    return tuple({t for t in (w.strip('#') for w in text.lower().translate(_TRANS_MAP).split()) if is_valid_token(t)})

# print(tokenizer('а где живет белая лöощадь 74? #1039729'))