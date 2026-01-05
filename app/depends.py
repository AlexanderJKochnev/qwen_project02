# app/depends.py
from typing import Callable, Any, Dict, Awaitable
from app.core.utils.translation_utils import fill_missing_translations


def get_translator_func() -> Callable[[Dict[str, Any], bool], Awaitable[Dict[str, Any]]]:
    return fill_missing_translations