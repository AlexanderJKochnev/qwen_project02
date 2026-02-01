# app/depends.py
from typing import Callable, Any, Dict, Awaitable, Optional
# from app.core.utils.translation_utils import fill_missing_translations
from app.core.utils import fill_missing_translations


def get_translator_func() -> Callable[[Dict[str, Any], Optional[bool]], Awaitable[Dict[str, Any]]]:
    return fill_missing_translations
