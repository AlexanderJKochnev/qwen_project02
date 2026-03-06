# app.suport.ollama.model.py
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, BigInteger, DateTime, Integer, JSON, CheckConstraint, Float
# from sqlalchemy.dialects.postgresql import JSONB  # Если используете PostgreSQL
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models.base_model import Base, BaseAt


class Ollama(Base, BaseAt):
    """
         список загружегннных  ll моделей
    """
    # Первичный ключ
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Основные поля (с индексом на model)
    model: Mapped[str] = mapped_column(String(255), index=True)
    modified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    digest: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)

    # Поля, поднятые из details
    parent_model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    format: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    family: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    parameter_size: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    quantization_level: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    def __str__(self):
        return self.model or ""

    # def __repr__(self) -> str:
    #     return f"<LLModel(model={self.model}, size={self.size})>"


class Prompt(Base, BaseAt):
    """
        модель для хранения ролей:
        translator: переводчик
        author: автор
        и др. (можно назвать как нибудь поинтересней чехов, полиглот
            {
          "model": "llama3",
          "prompt": "Translate the following...",
          "options": {
            "temperature": 0.1,
            "top_p": 0.1,
            "seed": 42,
            "num_ctx": 4096,
            "repeat_penalty": 1.0,
            "num_predict": 1000
          }
        }
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    system_prompt: Mapped[str] = mapped_column(String)

    # Параметры Ollama (Options)
    num_ctx: Mapped[int] = mapped_column(Integer, default=4096)
    temperature: Mapped[float] = mapped_column(Float, default=0.1)
    top_p: Mapped[float] = mapped_column(Float, default=0.1)
    top_k: Mapped[int] = mapped_column(Integer, default=40)
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    num_predict: Mapped[int] = mapped_column(Integer, default=1000)
    repeat_penalty: Mapped[float] = mapped_column(Float, default=1.1)
    stop: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    __table_args__ = (CheckConstraint('temperature BETWEEN 0.0 AND 2.0', name='temp_range'),
                      CheckConstraint('top_p BETWEEN 0.0 AND 1.0', name='top_p_range'),
                      CheckConstraint('num_predict >= -1', name='predict_range'),)

    def __str__(self):
        return self.role or ""


class ISOLanguage(Base, BaseAt):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # ISO 639-3 (3 буквы) — отличный первичный ключ, так как он уникален и постоянен
    iso_639_3: Mapped[str] = mapped_column(String(3), primary_key=True)
    # ISO 639-1 (2 буквы) — может быть NULL для редких языков
    iso_639_1: Mapped[Optional[str]] = mapped_column(String(2), unique=True, index=True, nullable=True)

    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ru: Mapped[str] = mapped_column(String(100), nullable=False)

    def __str__(self):
        return f"{self.iso} {self.name_en}" or ""
