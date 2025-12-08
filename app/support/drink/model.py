# app/support/drink/model.py
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import DECIMAL

from app.core.config.project_config import settings
from app.core.models.base_model import (Base, BaseAt, boolnone, descr, str_null_false, str_null_true)
# from app.core.models.image_mixin import ImageMixin
from app.core.utils.common_utils import plural

if TYPE_CHECKING:
    from app.support.sweetness.model import Sweetness
    from app.support.subcategory.model import Subcategory
    from app.support.subregion.model import Subregion


class Lang:
    __abstract__ = True
    title: Mapped[str_null_false]
    title_ru: Mapped[str_null_true]
    title_fr: Mapped[str_null_true]

    subtitle: Mapped[str_null_true]
    subtitle_ru: Mapped[str_null_true]
    subtitle_fr: Mapped[str_null_true]

    description: Mapped[descr]
    description_ru: Mapped[descr]
    description_fr: Mapped[descr]

    recommendation: Mapped[descr]
    recommendation_ru: Mapped[descr]
    recommendation_fr: Mapped[descr]

    madeof: Mapped[descr]
    madeof_ru: Mapped[descr]
    madeof_fr: Mapped[descr]


class Drink(Base, BaseAt, Lang):
    __table_args__ = (CheckConstraint('alc >= 0 AND alc <= 100.00', name='alc_range_check'),
                      CheckConstraint('sugar >= 0 AND sugar <= 100.00', name='sugar_range_check'),
                      UniqueConstraint('title', 'subtitle', name='uq_title_subtitle_unique'),
                      Index('drink_trigram_idx',
                            'title', 'title_ru', 'title_fr',
                            'subtitle', 'subtitle_ru', 'subtitle_fr',
                            'description', 'description_ru', 'description_fr',
                            'recommendation', 'recommendation_ru', 'recommendation_fr',
                            'madeof', 'madeof_ru', 'madeof_fr',
                            'age',
                            postgresql_using='gin',
                            postgresql_ops={
                                'title': 'gin_trgm_ops', 'title_ru': 'gin_trgm_ops', 'title_fr': 'gin_trgm_ops',
                                'subtitle': 'gin_trgm_ops', 'subtitle_ru': 'gin_trgm_ops', 'subtitle_fr': 'gin_trgm_ops',
                                'description': 'gin_trgm_ops', 'description_ru': 'gin_trgm_ops', 'description_fr': 'gin_trgm_ops',
                                'recommendation': 'gin_trgm_ops', 'recommendation_ru': 'gin_trgm_ops', 'recommendation_fr': 'gin_trgm_ops',
                                'madeof': 'gin_trgm_ops', 'madeof_ru': 'gin_trgm_ops', 'madeof_fr': 'gin_trgm_ops',
                                'age': 'gin_trgm_ops'
                            }))
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'drink'
    plural_name = plural(single_name)
    # наименование на языке производителя
    alc = mapped_column(DECIMAL(6, 2), nullable=True, default=0.0)
    # alc: Mapped[percent]
    sugar = mapped_column(DECIMAL(6, 2), nullable=True)  # , default = 0.0)
    # sugar: Mapped[percent]
    # aging: Mapped[ion]
    age: Mapped[str_null_true]
    sparkling: Mapped[boolnone]
    # Foreign Keys on-to-many
    subcategory_id: Mapped[int] = mapped_column(ForeignKey("subcategories.id"), nullable=False)
    subregion_id: Mapped[int] = mapped_column(ForeignKey("subregions.id"), nullable=False)
    sweetness_id: Mapped[int] = mapped_column(ForeignKey("sweetness.id"), nullable=True)

    # Relationships fields (
    subcategory: Mapped["Subcategory"] = relationship(back_populates="drinks")
    subregion: Mapped["Subregion"] = relationship(back_populates="drinks")
    sweetness: Mapped["Sweetness"] = relationship(back_populates="drinks")

    # обратная связь
    items = relationship("Item", back_populates=single_name,
                         cascade=cascade,
                         lazy=lazy)

    # Связь через промежуточную модель
    # food_associations = relationship("DrinkFood", back_populates="drink", cascade="all, delete-orphan")
    # foods = relationship("Food", secondary="drink_food_associations", viewonly=True, lazy="selectin")

    # Прямые связи с промежуточной таблицей
    food_associations = relationship("DrinkFood",
                                     back_populates="drink",
                                     cascade="all, delete-orphan",
                                     overlaps="foods")
    foods = relationship("Food",
                         secondary="drink_food_associations",
                         back_populates="drinks",
                         lazy="selectin",
                         viewonly=False,  # чтобы можно было использовать в form
                         overlaps="food_associations,drink")

    varietal_associations = relationship(
        "DrinkVarietal", back_populates="drink", cascade="all, delete-orphan", overlaps="varietals"
    )
    varietals = relationship("Varietal",
                             secondary="drink_varietal_associations",
                             back_populates="drinks",
                             lazy="selectin", viewonly=False, overlaps="varietal_associations,drink")

    # Важно: viewonly=False — позволяет SQLAlchemy корректно обновлять связь через .foods

    def __str__(self):
        return f"{self.title}"


class DrinkFood(Base):
    __tablename__ = "drink_food_associations"

    drink_id = Column(Integer, ForeignKey("drinks.id"), primary_key=True)
    food_id = Column(Integer, ForeignKey("foods.id"), primary_key=True)

    # Relationships
    drink = relationship("Drink", back_populates="food_associations", overlaps='foods')
    food = relationship("Food", back_populates="drink_associations", overlaps='drinks,foods')

    def __str__(self):
        return f"Drink {self.drink_id} - Food {self.food_id}"


class DrinkVarietal(Base):
    __tablename__ = "drink_varietal_associations"
    __table_args__ = (CheckConstraint('percentage >= 0 AND percentage <= 100.00',
                                      name='percentage_range_check'),)

    drink_id = Column(Integer, ForeignKey("drinks.id"), primary_key=True)
    varietal_id = Column(Integer, ForeignKey("varietals.id"), primary_key=True)
    percentage = mapped_column(DECIMAL(6, 2), nullable=True, default=100.0)

    # Relationships
    drink = relationship("Drink", back_populates="varietal_associations", overlaps='varietals')
    varietal = relationship("Varietal", back_populates="drink_associations", overlaps='drinks,varietals')

    def __str__(self):
        # return f"Drink {self.drink_id} - Varietal {self.food_id} (Percentage: {self.percentage})"
        return f"Varietal {self.varietal_id} (Percentage: {self.percentage})"
