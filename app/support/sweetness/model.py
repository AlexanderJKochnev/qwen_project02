# app/support/sweetness/model.py

from sqlalchemy.orm import relationship
from app.core.config.project_config import settings
from app.core.models.base_model import BaseFull, plural
from app.service_registry import registers_search_update


@registers_search_update("item")
class Sweetness(BaseFull):
    # Обратная связь: один ко многим
    """drinks: Mapped[List["Drink"]] = relationship("Drink",  # noqa F821
                                                 back_populates="sweetness",
                                                 cascade="all, delete-orphan")
    """
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'sweetness'
    plural_name = plural(single_name)
    drinks = relationship("Drink", back_populates=single_name,
                          cascade=cascade,
                          lazy=lazy)
