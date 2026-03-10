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
    STATUS: Mapped[str] = mapped_column(String(255), index=True)
    DISPLAY_NAME: Mapped[str] = mapped_column(String(255), index=True)
    PRODUCER_TITLE: Mapped[str] = mapped_column(String(255), index=True)
    PRODUCER_NAME: Mapped[str] = mapped_column(String(255), index=True)
    WINE: Mapped[str] = mapped_column(String(255), index=True)
    COUNTRY: Mapped[str] = mapped_column(String(255), index=True)
    REGION: Mapped[str] = mapped_column(String(255), index=True)
    SUB_REGION: Mapped[str] = mapped_column(String(255), index=True)
    SITE: Mapped[str] = mapped_column(String(255), index=True)
    PARCEL: Mapped[str] = mapped_column(String(255), index=True)
    COLOUR: Mapped[str] = mapped_column(String(255), index=True)
    TYPE: Mapped[str] = mapped_column(String(255), index=True)
    SUB_TYPE: Mapped[str] = mapped_column(String(255), index=True)
    DESIGNATION: Mapped[str] = mapped_column(String(255), index=True)
    CLASSIFICATION: Mapped[str] = mapped_column(String(255), index=True)
    VINTAGE_CONFIG: Mapped[str] = mapped_column(String(255), index=True)
    FIRST_VINTAGE: Mapped[str] = mapped_column(String(255), index=True)
    FINAL_VINTAGE: Mapped[str] = mapped_column(String(255), index=True)
    DATE_ADDED: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    DATE_UPDATED: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    REFERENCE: Mapped[str] = mapped_column(String(255), index=True)

    def __str__(self):
        return self.LWIN or ""
