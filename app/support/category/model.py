# app/support/category/model.py
from __future__ import annotations

from sqlalchemy.orm import relationship

from app.core.config.project_config import settings
from app.core.models.base_model import BaseFull, plural


class Category(BaseFull):
    lazy = settings.LAZY
    single_name = 'category'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
    # Обратная связь: один ко многим
    subcategories = relationship(
        "Subcategory", back_populates=single_name, cascade=cascade, lazy=lazy
    )
