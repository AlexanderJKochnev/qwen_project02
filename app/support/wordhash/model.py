# app/support/wordhash/model.py
# список всех слов с хэшем
from __future__ import annotations
from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from app.core.models.base_model import Base, Hash
from app.core.config.project_config import settings


class WordHash(Base, Hash):
    """
        таблица всех слов в базе данных
        нужна для автозаполнения при поиске
    """
    # id: Mapped[int_pk]
    # hash: Mapped[int] = mapped_column(BIGINT, nullable = False, index = True)
    lazy = settings.LAZY
    word: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)
    freq: Mapped[str] = mapped_column(Integer, nullable=False, default=0)
    mainword_id: Mapped[int | None] = mapped_column(ForeignKey("mainwords.id",
                                                               ondelete="SET NULL"),
                                                    nullable=True, index=True)
    mainword: Mapped["MainWord"] = relationship("MainWord", back_populates="wordhashs")

    def __str__(self):
        # переоопределять в особенных формах
        # or "" на всякий случай если обязательное поле вдруг окажется необязательным и пустым
        return f'{self.word}: {hash}'


class MainWord(Base, Hash):
    """Таблица канонических форм и лидеров синонимических групп"""
    # __tablename__ = "mainwords"
    lazy = settings.LAZY
    word: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=True)

    # Связь с исходными формами
    wordhashs: Mapped[list["WordHash"]] = relationship(back_populates="mainword")


class Trichin(Base):
    """
        таблица синонимов русского языка
    """
    word: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=False)
    synonym: Mapped[str] = mapped_column(String, nullable=False, index=True, unique=False)