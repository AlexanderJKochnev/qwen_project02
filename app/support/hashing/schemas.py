# app.support.hashing.schemas.py
from typing import Optional
from app.core.schemas.base import PkSchema, BaseModel


class CustomReadSchema:
    word: str
    hash: int
    freq: int


class WordHashRead(PkSchema, CustomReadSchema):
    pass


class WordHashCreate(BaseModel, CustomReadSchema):
    pass


class WordHashUpdate(PkSchema):
    word: Optional[str] = None
    hash: Optional[int] = None
    freq: Optional[int] = None

