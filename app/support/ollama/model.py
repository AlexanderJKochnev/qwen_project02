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
            "num_predict": 1000,
            "min_p": 0.05,                // новый параметр qwen3.5
            "typical_p": 0.9,             // баланс типичности и креативности
            "frequency_penalty": 0.3,      // легкий штраф за частые слова
            "presence_penalty": 0.2        // поощрение новых тем
          }
        }
    """
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # название промпта
    role: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # промпт
    system_prompt: Mapped[str] = mapped_column(String)
    # Параметры Ollama (Options)
    # Размер контекстного окна (токенов). Влияет на объем «памяти» модели.
    # Диапазон: от 1 до лимита модели (обычно 4096-128000).
    # Перевод: 2048 (достаточно для коротких фраз). Описания: 4096-8192.
    num_ctx: Mapped[int] = mapped_column(Integer, default=8192)

    # Креативность/случайность. 0 — строгость, 2 — хаос.
    # Перевод: 0.1 (макс. точность). Описания: 0.7–0.8 (живой язык).
    temperature: Mapped[float] = mapped_column(Float, default=0.1)

    # Nucleus sampling. Отсекает хвост маловероятных токенов, сумма вероятностей которых > P.
    # Диапазон: 0–1. Перевод: 0.1 (минимум вариаций). Описания: 0.9 (больше эпитетов).
    top_p: Mapped[float] = mapped_column(Float, default=0.1)

    # Ограничивает выбор N самыми вероятными токенами.
    # Диапазон: 1–100. Перевод: 10–20 (строго по делу). Описания: 40–60 (разнообразие).
    top_k: Mapped[int] = mapped_column(Integer, default=40)

    # Зерно генерации для повторяемости результата.
    # Любое целое число. Для тестов ставят фиксированное (напр. 42), для работы — Null.
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Максимальное количество генерируемых токенов в ответе.
    # Перевод: 50–100. Описания: 300–1000 (в зависимости от желаемой длины).
    num_predict: Mapped[int] = mapped_column(Integer, default=1000)

    # Штраф за повторение слов. Больше значение — меньше самоповторов.
    # Диапазон: 1.0–2.0. Перевод: 1.0–1.1. Описания: 1.1–1.2 (чтобы не частить с прилагательными).
    repeat_penalty: Mapped[float] = mapped_column(Float, default=1.1)

    # Список стоп-последовательностей, на которых модель прервет генерацию.
    # Используется для предотвращения «галлюцинаций» или лишних пояснений.
    stop: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Альтернатива Top-P. Отсекает токены, чья вероятность ниже P от вероятности лидера.
    # Диапазон: 0–1. Рекомендуется 0.05 для баланса между качеством и креативностью.
    min_p: Mapped[float] = mapped_column(Float, default=None)  # 0.05)

    # Typical sampling. Снижает риск «зацикливания» на скучных словах.
    # Диапазон: 0–1. Значение 0.9-1.0 помогает делать текст более естественным для людей.
    typical_p: Mapped[float] = mapped_column(Float, default=None)  # 0.9)

    # Штраф за использование слов в зависимости от того, как часто они уже встречались.
    # Перевод: 0.0. Описания: 0.3–0.5 (избавляет от слов-паразитов в тексте).
    frequency_penalty: Mapped[float] = mapped_column(Float, default=None)  # 0.3)

    # Штраф за само упоминание темы. Поощряет переход к новым идеям/аспектам.
    # Перевод: 0.0. Описания: 0.2–0.4 (чтобы описание было разносторонним).
    presence_penalty: Mapped[float] = mapped_column(Float, default=None)  # 0.2)

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
        return f"{self.iso_639_3} {self.name_en}" or ""
