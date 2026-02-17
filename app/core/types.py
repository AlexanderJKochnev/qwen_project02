# app.core.types.py
from typing import TypeVar
from sqlalchemy.orm import DeclarativeBase, DeclarativeMeta, MapperProperty

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)