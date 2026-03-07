# app.suport.ollama.schemas.py
from datetime import datetime
from typing import Optional, List
from pydantic import model_validator, ConfigDict, Field, field_validator, computed_field
from app.core.schemas.base import PkSchema, BaseModel
# from app.support.ollama.model import Prompt


class ProptionCustom(BaseModel):
    # system_prompt: Optional[str] = Field(None, description="Инструкция для модели")
    num_ctx: Optional[int] = Field(4096, ge=1, le=131072)
    temperature: Optional[float] = Field(0.1, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(0.1, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(40, ge=0)
    seed: Optional[int] = None
    num_predict: Optional[int] = Field(1000, ge=-1)
    repeat_penalty: Optional[float] = Field(1.1, ge=0.0, le=2.0)
    stop: Optional[List[str]] = None

    # Новые поля:
    min_p: Optional[float] = Field(
        0.05, ge=0.0, le=1.0, description="Минимальная вероятность относительно лидера"
    )
    typical_p: Optional[float] = Field(0.9, ge=0.0, le=1.0, description="Типичная вероятность (Typical sampling)")
    frequency_penalty: Optional[float] = Field(0.3, ge=0.0, le=2.0, description="Штраф за частоту слов")
    presence_penalty: Optional[float] = Field(0.2, ge=0.0, le=2.0, description="Штраф за само наличие слов")
    thinking: Optional[bool] = False

    @field_validator('stop')
    @classmethod
    def validate_stop_sequences(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) > 10:
            raise ValueError("Слишком много стоп-последовательностей (макс. 10)")
        return v


class ProptionCreate(ProptionCustom):
    preset: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zа-я0-9_-]+$")


class ProptionUpdate(ProptionCustom):
    preset: Optional[str] = Field(..., min_length=2, max_length=50, pattern=r"^[a-zа-я0-9_-]+$")


class ProptionRead(PkSchema, ProptionCreate):
    id: int


class PromptCreate(BaseModel):
    """Модель для POST запроса: role и system_prompt обязательны"""
    role: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zа-я0-9_-]+$")
    system_prompt: str = Field(..., min_length=10)


class PromptUpdate(BaseModel):
    """Модель для PATCH запроса: все поля необязательны"""
    # Мы наследуем всё от Base, где поля уже Optional.
    # Поле role обычно не меняют через PATCH, но если нужно — добавим:
    role: Optional[str] = Field(None, min_length=2, max_length=50)

    model_config = ConfigDict(extra='forbid')  # Запрещает передавать лишние поля


class PromptRead(PkSchema, PromptCreate):
    id: int


"""
то что возвращает ollama.asyncclient.list()
[
  [
    "models",
    [
      {
        "model": "deepseek-r1:7b",
        "modified_at": "2026-02-28T21:00:43.813787Z",
        "digest": "755ced02ce7befdb13b7ca74e1e4d08cddba4986afdb63a480f2c93d3140383f",
        "size": 4683075440,
        "details": {
          "parent_model": "",
          "format": "gguf",
          "family": "qwen2",
          "families": [
            "qwen2"
          ],
          "parameter_size": "7.6B",
          "quantization_level": "Q4_K_M"
        }
      },
    ]
  ]
]
"""


class LlmResponseSchema(BaseModel):
    """ получает на входе вложенный словарь LLM response и возвращает плоский словарь Ollama """
    model: str
    modified_at: datetime
    digest: Optional[str] = None
    size: Optional[int] = None
    # details: Optional[dict] = None
    parent_model: Optional[str] = None
    format: Optional[str] = None
    family: Optional[str] = None
    # families: Optional[List[str]] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None
    
    @computed_field
    @property
    def size_gb(self) -> Optional[float]:
        """Возвращает размер модели в гигабайтах с округлением до 2 знаков."""
        if self.size is None:
            return None
        return round(self.size / (1024 ** 3), 2)

    @model_validator(mode='before')
    @classmethod
    def flatten_details(cls, data: dict) -> dict:
        # Извлекаем словарь details
        details = data.pop('details', {})
        # Объединяем основной словарь с содержимым details
        return {**data, **details}


class OllamaCreate(BaseModel):
    model: str
    modified_at: datetime
    digest: Optional[str] = None
    size: Optional[int] = None
    # details: Optional[dict] = None
    parent_model: Optional[str] = None
    format: Optional[str] = None
    family: Optional[str] = None
    # families: Optional[List[str]] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None


class OllamaUpdate(BaseModel):
    model: Optional[str] = None
    modified_at: Optional[datetime] = None
    digest: Optional[str] = None
    size: Optional[int] = None
    parent_model: Optional[str] = None
    format: Optional[str] = None
    family: Optional[str] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None


class OllamaRead(PkSchema, OllamaCreate):
    size: Optional[int] = Field(exclude=True)

    @computed_field
    @property
    def size_gb(self) -> Optional[float]:
        """Возвращает размер модели в гигабайтах с округлением до 2 знаков."""
        if self.size is None:
            return None
        return round(self.size / (1024 ** 3), 2)

class ISOLanguageCreate(BaseModel):
    iso_639_3: str
    iso_639_1: Optional[str] = None
    name_en: str
    name_ru: str


class ISOLanguageUpdate(BaseModel):
    iso_639_3: Optional[str]
    iso_639_1: Optional[str] = None
    name_en: Optional[str]
    name_ru: Optional[str]


class ISOLanguageRead(ISOLanguageCreate):
    id: int
