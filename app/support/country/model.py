# app/support/country/model.py
from __future__ import annotations
from sqlalchemy.orm import relationship
from app.core.models.base_model import BaseFull
from app.service_registry import registers_search_update


@registers_search_update("region.subregion.drink.item")
class Country(BaseFull):
    regions = relationship("Region", back_populates="country", lazy="selectin", cascade="all, delete-orphan")
