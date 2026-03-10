# app.support.lwin.model.py

from datetime import datetime
from sqlalchemy import String, DateTime
# from sqlalchemy.dialects.postgresql import JSONB  # Если используете PostgreSQL
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models.base_model import Base


class Lwin(Base):
    """
         lwin
    """
    # Первичный ключ
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    LWIN: Mapped[str] = mapped_column(String(255), index=True)
    STATUS: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    DISPLAY_NAME: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    PRODUCER_TITLE: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    PRODUCER_NAME: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    WINE: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    COUNTRY: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    REGION: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    SUB_REGION: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    SITE: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    PARCEL: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    COLOUR: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    TYPE: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    SUB_TYPE: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    DESIGNATION: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    CLASSIFICATION: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    VINTAGE_CONFIG: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    FIRST_VINTAGE: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    FINAL_VINTAGE: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    DATE_ADDED: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    DATE_UPDATED: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    # REFERENCE: Mapped[str] = mapped_column(String(255), index=True, nullable=True)

    def __str__(self):
        return self.LWIN or ""
