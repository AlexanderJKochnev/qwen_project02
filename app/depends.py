# app/core/depends.py
from typing import Dict, Any
from fastapi import Depends

from app.core.utils.translation_utils import fill_missing_translations


async def apply_translations(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dependency function to apply translations to data
    """
    return await fill_missing_translations(data)


def get_translation_dependency():
    """
    Returns the translation dependency function that can be used with Depends
    """
    return Depends(apply_translations)
