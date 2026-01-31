# app/support/varietal/model.py
from __future__ import annotations

from typing import List, TYPE_CHECKING

from sqlalchemy.orm import Mapped, relationship
from app.core.config.project_config import settings
from app.core.models.base_model import BaseFull, plural
from app.service_registry import registers_search_update

if TYPE_CHECKING:
    from app.support.drink.model import DrinkVarietal


@registers_search_update("drink.item")
class Varietal(BaseFull):
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'varietal'
    plural_name = plural(single_name)
    # Связь с промежуточной таблицей
    drink_associations: Mapped[List["DrinkVarietal"]] = relationship("DrinkVarietal",
                                                                     back_populates="varietal",
                                                                     cascade="all, delete-orphan",
                                                                     overlaps="drinks,varietals")
    drinks = relationship("Drink", secondary="drink_varietal_associations", back_populates="varietals",
                          lazy="selectin", overlaps="drink_associations,varietal,drink,varietal_associations")

    """ alternative version
    @property
    def drinks(self):
        return [association.drink for association in self.drink_associations]
    """
