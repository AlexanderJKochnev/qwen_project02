# app/support/food/model.py
from __future__ import annotations
from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from app.core.config.project_config import settings
from app.core.models.base_model import BaseFull, plural
from app.service_registry import registers_search_update

if TYPE_CHECKING:
    from app.support.drink.model import DrinkFood
    from app.support.superfood.model import Superfood
    from app.support.drink.model import Drink


@registers_search_update("drinks.items")
class Food(BaseFull):
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'food'
    plural_name = plural(single_name)

    superfood_id: Mapped[int] = mapped_column(ForeignKey("superfoods.id"), nullable=True)
    superfood: Mapped["Superfood"] = relationship(back_populates=plural_name, lazy=lazy)

    # Связь с промежуточной таблицей
    """
    drink_associations: Mapped[List["DrinkFood"]] = relationship("DrinkFood",
                                                                 back_populates="food",
                                                                 cascade="all, delete-orphan",
                                                                 overlaps="drinks,foods")
    drinks = relationship("Drink", secondary="drink_food_associations", back_populates="foods",
                          lazy="selectin", overlaps="drink_associations,food,drink,food_associations")
    """
    # --- NEW VERSION ---

    # 1. Связь через промежуточную таблицу (Association Object)
    drink_associations: Mapped[List["DrinkFood"]] = relationship(
        back_populates="food", cascade="all, delete-orphan"
    )

    # 2. Прямая связь Many-to-Many
    drinks: Mapped[List["Drink"]] = relationship(
        secondary="drink_food_associations", back_populates="foods", viewonly=True
        # Рекомендуется viewonly, если работаете через ассоциации
    )
