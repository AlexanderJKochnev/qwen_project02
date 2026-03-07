# app.core.types.py
from typing import TypeVar
from sqlalchemy.orm import DeclarativeMeta
from enum import Enum


ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class Preset(str, Enum):
    translation = "translation"
    balanced = "balanced"
    quality = "quality"