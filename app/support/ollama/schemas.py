# app.suport.ollama.schemas.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import model_validator, ConfigDict, Field, field_validator
from app.core.schemas.base import PkSchema, BaseModel
# from app.support.ollama.model import Prompt


class CustomRead(BaseModel):
    """Схема только для блока options в API Ollama"""
    num_ctx: int
    temperature: float
    top_p: float
    top_k: int
    seed: Optional[int]
    num_predict: int
    repeat_penalty: float
    stop: Optional[List[str]]


class PromptRead(BaseModel):
    """
        универсальная модель для
        chat: message и
        generate: prompt, system
    """
    model_config = ConfigDict(from_attributes=True)

    # model: str = "llama3"
    options: CustomRead
    stream: bool = False

    # Эти поля взаимоисключающие для разных методов
    messages: Optional[List[Dict[str, str]]] = None  # Для .chat()
    prompt: Optional[str] = None  # Для .generate()
    system: Optional[str] = None  # Для .generate() переопределяет системный промпт

    @classmethod
    def create_chat_payload(cls, db_obj: Any, user_text: str) -> "PromptRead":
        """Структура для ollama.chat"""
        return cls(
            messages=[{"role": "system", "content": db_obj.system_prompt},
                      {"role": "user", "content": user_text}], options=CustomRead(**db_obj.__dict__)
        )

    @classmethod
    def create_generate_payload(cls, db_obj: Any, user_text: str) -> "PromptRead":
        """Структура для ollama.generate"""
        return cls(
            prompt=user_text, system=db_obj.system_prompt,  # В generate системник передается отдельным полем
            options=CustomRead(**db_obj.__dict__)
        )


class PromptRequest(PromptRead):
    """
        возвращает универсальную модель для
        chat: message и
        generate: prompt, system
        с подставленной моделью.
        Так как разные поля будут переводить разные роли (переводчик для наименовений, автор для описаний)
        нужно что бы в каждой роди использовалась одна и таже модель
    """
    model: str = "llama3"


class Custom(BaseModel):
    system_prompt: Optional[str] = Field(None, description="Инструкция для модели")
    num_ctx: Optional[int] = Field(4096, ge=1, le=131072)
    temperature: Optional[float] = Field(0.1, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(0.1, ge=0.0, le=1.0)
    top_k: Optional[int] = Field(40, ge=0)
    seed: Optional[int] = None
    num_predict: Optional[int] = Field(1000, ge=-1)
    repeat_penalty: Optional[float] = Field(1.1, ge=0.0, le=2.0)
    stop: Optional[List[str]] = None

    # Пример кастомной валидации (Pydantic 2 style)

    @field_validator('stop')
    @classmethod
    def validate_stop_sequences(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) > 10:
            raise ValueError("Слишком много стоп-последовательностей (макс. 10)")
        return v


class PromptCreate(Custom):
    """Модель для POST запроса: role и system_prompt обязательны"""
    role: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zа-я0-9_-]+$")
    system_prompt: str = Field(..., min_length=10)


class PromptUpdate(Custom):
    """Модель для PATCH запроса: все поля необязательны"""
    # Мы наследуем всё от Base, где поля уже Optional.
    # Поле role обычно не меняют через PATCH, но если нужно — добавим:
    role: Optional[str] = Field(None, min_length=2, max_length=50)

    model_config = ConfigDict(extra='forbid')  # Запрещает передавать лишние поля


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
    pass
