# app.support.gemma.schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List


class BenchmarkRequest(BaseModel):
    text: str
    target_langs: List[str] = ["russian", "spanish", "chinese", "french", "german", "italy"]
    model_levels: List[int] = [1, 2, 3, 4]  # Список уровней для сравнения
    industry: str = "wine"  # wine, trade или general
    temperatures: List[float] = [0.0, 0.3, 0.7, 1.0]


class TranslationRequest(BaseModel):
    # Обязательные
    text: str
    target_lang: str

    # Настройки с дефолтами (вынесены в роутер)
    model_level: int = Field(default=1, ge=1, le=3, description="1: 2b, 2: 9b, 3: 27b")
    interaction_type: str = Field(default="chat", pattern="^(chat|generate)$")

    # Параметры модели (для подбора "на лету")
    temperature: float = Field(default=0.1, ge=0.0, le=1.0)
    num_predict: int = Field(default=1000, description="Макс. длина ответа")
    top_p: float = Field(default=0.9)
    keep_alive: str = Field(default="5m", description="Время удержания в GPU")
    stop: Optional[List[str]] = Field(default=None, description="Стоп-слова")
