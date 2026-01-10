# app/support/superfood/model.py

from __future__ import annotations   # ОБЯЗАТЕЛЬНО ДЛЯ FOREIGN RELATIONSHIPS
from sqlalchemy.orm import relationship

from app.core.config.project_config import settings
from app.core.models.base_model import BaseFull, plural


class Superfood(BaseFull):
    lazy = settings.LAZY
    single_name = 'superfood'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
    # Обратная связь: один ко многим
    foods = relationship("Food", back_populates=single_name, cascade=cascade, lazy=lazy)
