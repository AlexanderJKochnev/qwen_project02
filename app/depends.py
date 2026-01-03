# app/depends.py
from typing import Dict, Any, Callable
from fastapi import Depends
from app.core.utils.translation_utils import fill_missing_translations


def get_fill_missing_translations_dependency() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Dependency to provide fill_missing_translations function"""
    return fill_missing_translations
