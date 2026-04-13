# app/support/hashing/model.py
# список всех слов с хэшем
from __future__ import annotations
from sqlalchemy import BigInteger, String, Integer
from sqlalchemy.orm import mapped_column, Mapped
from app.core.models.base_model import Base


class WordHash(Base):
    """
        таблица всех слов в базе данных
        нужна для автозаполнения при поиске
    """
    word: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    hash: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    freq: Mapped[str] = mapped_column(Integer, nullable=False, default=0)

    def __str__(self):
        # переоопределять в особенных формах
        # or "" на всякий случай если обязательное поле вдруг окажется необязательным и пустым
        return self.word or ""
