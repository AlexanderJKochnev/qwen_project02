# app/support/drink/model.py
from __future__ import annotations

from typing import TYPE_CHECKING, List

from sqlalchemy import (CheckConstraint, Column, ForeignKey, Integer, String, Index)
from sqlalchemy.orm import Mapped, mapped_column, relationship, declared_attr, validates
from sqlalchemy.types import DECIMAL
from decimal import Decimal
from app.core.config.project_config import settings
from app.core.models.base_model import (Base, BaseAt, boolnone, descr, plural, str_null_false, str_null_true)
from app.service_registry import registers_search_update

if TYPE_CHECKING:
    # from app.support.sweetness.model import Sweetness
    # from app.support.subcategory.model import Subcategory
    # from app.support.subregion.model import Subregion
    # from app.support.food.model import Food
    from app.support import (Source, Sweetness, Subcategory, Food, Producer, VintageConfig,
                             Classification, Designation, Site, Parcel)


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

    """
    title_xx: Mapped[str_null_true]
    subtitle_xx: Mapped[str_null_true]
    description_xx: Mapped[descr]
    recommendation_xx: Mapped[descr]
    madeof_xx: Mapped[descr]
    """

    title_es: Mapped[str_null_true]
    subtitle_es: Mapped[str_null_true]
    description_es: Mapped[descr]
    recommendation_es: Mapped[descr]
    madeof_es: Mapped[descr]

    title_it: Mapped[str_null_true]
    subtitle_it: Mapped[str_null_true]
    description_it: Mapped[descr]
    recommendation_it: Mapped[descr]
    madeof_it: Mapped[descr]

    title_de: Mapped[str_null_true]
    subtitle_de: Mapped[str_null_true]
    description_de: Mapped[descr]
    recommendation_de: Mapped[descr]
    madeof_de: Mapped[descr]

    title_zh: Mapped[str_null_true]
    subtitle_zh: Mapped[str_null_true]
    description_zh: Mapped[descr]
    recommendation_zh: Mapped[descr]
    madeof_zh: Mapped[descr]


class Lwn:
    """  для связи с lwin """
    __abstract__ = True
    lwin: Mapped[str | None] = mapped_column(String(7),
                                             CheckConstraint("lwin ~ '^[0-9]*$'", name="check_digits_only"),
                                             nullable=True, index=True
                                             )

    @validates("lwin")
    def validate_lwin(self, key, value):
        if value is not None:
            if not value.isdigit():
                raise ValueError("Поле должно содержать только цифры")
            if len(value) < 7:
                raise ValueError("Длина не должна меньше 7 символов")
            if len(value) > 7:
                raise ValueError("Длина не должна превышать 7 символов")
        return value

    anno: Mapped[str | None] = mapped_column(
        String(4), CheckConstraint("anno ~ '^[0-9]*$'", name="check_digits_only"), nullable=True, index=True
    )

    @validates("anno")
    def validate_anno(self, key, value):
        if value is not None:
            if not value.isdigit():
                raise ValueError("Поле должно содержать только цифры")
            if len(value) < 4:
                raise ValueError("Длина не должна меньше 4 символов")
            if len(value) > 4:
                raise ValueError("Длина не должна превышать 4 символов")
        return value


class ForeignOneToMany:
    __abstract__ = True
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True, index=True)
    producer_id: Mapped[int | None] = mapped_column(ForeignKey("producers.id"), nullable=True, index=True)
    vintageconfig_id: Mapped[int | None] = mapped_column(ForeignKey("vintageconfigs.id"), nullable=True, index=True)
    classification_id: Mapped[int | None] = mapped_column(ForeignKey("classifications.id"), nullable=True,
                                                          index=True)
    designation_id: Mapped[int | None] = mapped_column(ForeignKey("designations.id"), nullable=True, index=True)
    site_id: Mapped[int | None] = mapped_column(ForeignKey("sites.id"), nullable=False, index=True)
    parcel_id: Mapped[int | None] = mapped_column(ForeignKey("parcels.id"), nullable=True, index=True)

    @declared_attr
    def source(cls) -> Mapped["Source"]:
        return relationship(back_populates="drinks")

    @declared_attr
    def producer(cls) -> Mapped["Producer"]:
        return relationship(back_populates="drinks")

    @declared_attr
    def vintageconfig(cls) -> Mapped["VintageConfig"]:
        return relationship(back_populates="drinks")

    @declared_attr
    def classification(cls) -> Mapped["Classification"]:
        return relationship(back_populates="drinks")

    @declared_attr
    def designation(cls) -> Mapped["Designation"]:
        return relationship(back_populates="drinks")

    @declared_attr
    def parcel(cls) -> Mapped["Parcel"]:
        return relationship(back_populates="drinks")

    @declared_attr
    def site(cls) -> Mapped["Site"]:
        return relationship(back_populates="drinks")


class Vintage:
    __abstract__ = True
    first_vintage: Mapped[str | None] = mapped_column(
        String(4), CheckConstraint("first_vintage ~ '^[0-9]*$'", name="check_digits_only"), nullable=True, index=True
    )

    @validates("first_vintage")
    def validate_first_vintage(self, key, value):
        if value is not None:
            if not value.isdigit():
                raise ValueError("Поле должно содержать только цифры")
            if len(value) < 4:
                raise ValueError("Длина не должна меньше 4 символов")
            if len(value) > 4:
                raise ValueError("Длина не должна превышать 4 символов")
        return value

    last_vintage: Mapped[str | None] = mapped_column(
        String(4), CheckConstraint("last_vintage ~ '^[0-9]*$'", name="check_digits_only"), nullable=True, index=True
    )

    @validates("last_vintage")
    def validate_last_vintage(self, key, value):
        if value is not None:
            if not value.isdigit():
                raise ValueError("Поле должно содержать только цифры")
            if len(value) < 4:
                raise ValueError("Длина не должна меньше 4 символов")
            if len(value) > 4:
                raise ValueError("Длина не должна превышать 4 символов")
        return value


class DisplayName:
    __abstract__ = True
    display_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, index=True
    )


@registers_search_update("item")
class Drink(Base, BaseAt, Lang, ForeignOneToMany, Vintage, Lwn, DisplayName):
    lazy = settings.LAZY
    cascade = settings.CASCADE
    single_name = 'drink'
    plural_name = plural(single_name)
    # наименование на языке производителя
    alc: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 2), nullable=True, default=0.0)
    sugar: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 2), nullable=True)  # , default = 0.0)
    age: Mapped[str_null_true]
    sparkling: Mapped[boolnone]
    # Foreign Keys on-to-many
    subcategory_id: Mapped[int] = mapped_column(ForeignKey("subcategories.id"), nullable=False, index=True)
    # subregion_id: Mapped[int] = mapped_column(ForeignKey("subregions.id"), nullable=False, index=True)
    sweetness_id: Mapped[int | None] = mapped_column(ForeignKey("sweetness.id"), nullable=True, index=True)

    # Relationships fields (
    subcategory: Mapped["Subcategory"] = relationship(back_populates="drinks")
    # subregion: Mapped["Subregion"] = relationship(back_populates="drinks")
    sweetness: Mapped["Sweetness"] = relationship(back_populates="drinks")

    # обратная связь
    items = relationship("Item", back_populates=single_name,
                         cascade=cascade,
                         lazy=lazy)

    # Связь через промежуточную модель NEW
    # 1. Связь через промежуточную таблицу
    food_associations: Mapped[List["DrinkFood"]] = relationship(
        back_populates="drink",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # 2. Прямая связь Many-to-Many
    """
    foods: Mapped[List["Food"]] = relationship(
        secondary="drink_food_associations",
        back_populates="drinks",
        lazy="selectin",
        # viewonly=False, overlaps="food_associations,drink"
        # Загрузит список объектов Food автоматически
    )
    """
    varietal_associations = relationship(
        "DrinkVarietal",
        back_populates="drink",
        cascade="all, delete-orphan",
        # overlaps="varietals"
        lazy="selectin"
    )
    varietals = relationship("Varietal",
                             secondary="drink_varietal_associations",
                             back_populates="drinks",
                             lazy="selectin", viewonly=False, overlaps="varietal_associations,drink")

    # Важно: viewonly=False — позволяет SQLAlchemy корректно обновлять связь через .foods
    __table_args__ = (CheckConstraint('alc >= 0 AND alc <= 100.00', name='alc_range_check'),
                      CheckConstraint("(first_vintage IS NULL) OR (first_vintage >= 1000 AND first_vintage <= 3000)",
                                      name="check_first_vintage_range_or_null"),
                      CheckConstraint("(last_vintage IS NULL) OR (last_vintage >= 1000 AND last_vintage <= 3000)",
                                      name="check_last_vintage_range_or_null"),
                      # UniqueConstraint('title', 'subtitle', 'producer_id',
                      # 'site_id', 'parcel_id', 'lwn', 'anno', name='uq_title_subtitle_unique'),
                      Index("uq_title_unique", "title", "subtitle", "producer_id", "site_id",
                            "parcel_id", "lwin", "anno", "display_name",
                            unique=True, postgresql_nulls_not_distinct=True  # Ключевой параметр
                            ),
                      )

    def __str__(self):
        return f"{self.title}"


@registers_search_update("drink.item")
class DrinkFood(Base):
    __tablename__ = "drink_food_associations"
    drink_id: Mapped[int] = mapped_column(ForeignKey("drinks.id"), primary_key=True)
    food_id: Mapped[int] = mapped_column(ForeignKey("foods.id"), primary_key=True)

    # Связи с конкретными объектами
    drink: Mapped["Drink"] = relationship(back_populates="food_associations")
    food: Mapped["Food"] = relationship(back_populates="drink_associations")

    # --- PREVIOUS MESSAGE ---
    # drink_id = Column(Integer, ForeignKey("drinks.id"), primary_key=True)
    # food_id = Column(Integer, ForeignKey("foods.id"), primary_key=True)

    # Relationships
    # drink = relationship("Drink", back_populates="food_associations", overlaps='foods')
    # food = relationship("Food", back_populates="drink_associations", overlaps='drinks,foods')

    def __str__(self):
        return f"Drink {self.drink_id} - Food {self.food_id}"


@registers_search_update("drink.item")
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
