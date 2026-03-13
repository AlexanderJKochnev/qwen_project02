# app.support.source.model.py
"""
    источник записей
"""
from __future__ import annotations

from sqlalchemy.orm import relationship

from app.core.config.project_config import settings
from app.core.models.base_model import BaseFullFree, plural
from app.service_registry import registers_search_update


@registers_search_update("drink.item")
class Source(BaseFullFree):
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'source'
    plural_name = plural(single_name)
    drinks = relationship("Drink", back_populates=single_name,
                          cascade=cascade,
                          lazy=lazy)
