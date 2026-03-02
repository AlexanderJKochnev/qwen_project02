# app.suport.ollama.model.py
from datetime import datetime
from typing import Optional
from sqlalchemy import String, BigInteger, DateTime
# from sqlalchemy.dialects.postgresql import JSONB  # Если используете PostgreSQL
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models.base_model import Base


class Ollama(Base):

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
