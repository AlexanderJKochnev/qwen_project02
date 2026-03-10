# app.support.lwin.model.py

from datetime import datetime
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.models.base_model import Base


class Lwin(Base):
    """
         lwin
    """
    # Первичный ключ
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    lwin: Mapped[str] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    display_name: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    producer_title: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    producer_name: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    wine: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    country: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    region: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    sub_region: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    site: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    parcel: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    colour: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    type: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    sub_type: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    designation: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    classification: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    vintage_config: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    first_vintage: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    final_vintage: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    date_added: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    date_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    # REFERENCE: Mapped[str] = mapped_column(String(255), index=True, nullable=True)

    def __str__(self):
        return self.lwin or ""
