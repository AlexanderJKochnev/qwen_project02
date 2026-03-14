# app.support.vintage.model.py
from __future__ import annotations

from sqlalchemy.orm import relationship

from app.core.config.project_config import settings
from app.core.models.base_model import BaseFull, plural
from app.service_registry import registers_search_update


@registers_search_update("drink.item")
class VintageConfig(BaseFull):
    """
        конфигурация vintage:
        последовтельно год за годом
        не последжовательно:  год через два-три
        одноразовый выпуск
    """
    lazy = settings.LAZY
    single_name = 'vintageconfig'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
    # Обратная связь: many to one
    drinks = relationship(
        "Drink", back_populates=single_name, cascade=cascade, lazy=lazy
    )


@registers_search_update("drink.item")
class Classification(BaseFull):
    """
        классификация:
        Grand Cru, и т.п.
    """
    lazy = settings.LAZY
    single_name = 'classification'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
    # Обратная связь: many to one
    drinks = relationship(
        "Drink", back_populates=single_name, cascade=cascade, lazy=lazy
    )


@registers_search_update("producer.drink.item")
class Designation(BaseFull):
    """
        AOG AOC ...
    """
    lazy = settings.LAZY
    single_name = 'designation'
    plural_name = plural(single_name)
    cascade = settings.CASCADE
    # Обратная связь: many to one
    drinks = relationship(
        "Drink", back_populates=single_name, cascade=cascade, lazy=lazy
    )
