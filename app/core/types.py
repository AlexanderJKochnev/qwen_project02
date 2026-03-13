# app.core.types.py
from typing import TypeVar
# from sqlalchemy.orm import DeclarativeMeta
from app.core.models.base_model import Base


ModelType = TypeVar("ModelType", bound=Base)
# ModelType = TypeVar("ModelType", bound=DeclarativeMeta)
