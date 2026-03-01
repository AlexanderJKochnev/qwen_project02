# app.suport.ollama.schemas.py
from datetime import datetime
from typing import Optional, List
from app.core.schemas.base import PkSchema, BaseModel
from pydantic import model_validator

"""
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


class LLModels(BaseModel):
    model: str
    modified_at: datetime
    digest: Optional[str] = None
    size: Optional[int] = None
    # details: Optional[dict] = None
    parent_model: Optional[str] = None
    format: Optional[str] = None
    family: Optional[str] = None
    families: Optional[List[str]] = None
    parameter_size: Optional[str] = None
    quantization_level: Optional[str] = None

    @model_validator(mode='before')
    @classmethod
    def flatten_details(cls, data: dict) -> dict:
        # Извлекаем словарь details
        details = data.pop('details', {})
        # Объединяем основной словарь с содержимым details
        return {**data, **details}
