# app/support/parser/model.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (DateTime, ForeignKey, func, Integer, String, Text, text, Index,
                        UniqueConstraint, Computed)
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base_model import Base, BaseAt
from app.core.models.image_mixin import ImageMixin


class Registry(Base, BaseAt):
    """ адреса баз данных и базовые настройки """
    __tablename__ = 'registry'
    shortname: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id", ondelete="SET NULL"), nullable=True)
    status: Mapped["Status"] = relationship("Status", back_populates="registry")
    # базовый URL-префикс, которому должны соответствовать ссылки
    base_path: Mapped[str] = mapped_column(String(255), unique=False, index=True, nullable=True)
    # HTML-тег и атрибут для извлечения ссылок
    link_tag: Mapped[str] = mapped_column(String(255), unique=False, index=True, nullable=True)
    link_attr: Mapped[str] = mapped_column(String(255), unique=False, index=True, nullable=True)
    parent_selector: Mapped[str] = mapped_column(String(255), unique=False, index=True, nullable=True)
    timeout: Mapped[int] = mapped_column(Integer, unique=False, index=True, nullable=True)
    codes: Mapped[List["Code"]] = relationship("Code", back_populates="registry", cascade="all, delete-orphan")

    # Тег и атрибут для парсинга ссылок на продукты (Name)
    name_link_tag: Mapped[str] = mapped_column(String(255), nullable=True, default="a")
    name_link_attr: Mapped[str] = mapped_column(String(255), nullable=True, default="href")
    name_link_parent_selector: Mapped[str] = mapped_column(String(255), nullable=True, default="div#cont_txt")

    # Селектор для блока пагинации
    pagination_selector: Mapped[str] = mapped_column(
        String(255), nullable=True, default="div#cont_txt p:contains('Выберите страницу')"
    )
    pagination_link_tag: Mapped[str] = mapped_column(String(255), nullable=True, default="a")
    pagination_link_attr: Mapped[str] = mapped_column(String(255), nullable=True, default="href")

    def __str__(self):
        return self.shortname or ""


class Code(Base, BaseAt):

    code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    url: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    last_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=None)

    status: Mapped["Status"] = relationship("Status", back_populates="codes")
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id", ondelete="SET NULL"),
                                           nullable=True)
    registry: Mapped["Registry"] = relationship("Registry", back_populates="codes")
    registry_id: Mapped[int] = mapped_column(ForeignKey("registry.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    names: Mapped[List["Name"]] = relationship("Name", back_populates="code", cascade="all, delete-orphan")

    def __str__(self):
        return self.code or ""


class Name(Base, BaseAt):

    code_id: Mapped[int] = mapped_column(ForeignKey("codes.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), index=True)
    url: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped["Status"] = relationship("Status", back_populates="names")
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id", ondelete="SET NULL"), nullable=True)

    # Relationships с каскадным удалением
    code: Mapped["Code"] = relationship("Code", back_populates="names")
    raw_data: Mapped[Optional["Rawdata"]] = relationship(
        "Rawdata", back_populates="name", cascade="all, delete-orphan", uselist=False)
    images: Mapped[List["Image"]] = relationship("Image", back_populates="name", cascade="all, delete-orphan")


class Rawdata(Base, BaseAt):

    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"), unique=True)
    # body_html: Mapped[Optional[str]] = mapped_column(Text)
    # parsed_data: Mapped[Optional[str]] = mapped_column(Text)  # JSON or YAML formatted parsed data
    metadata_json: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    status: Mapped["Status"] = relationship("Status", back_populates="rawdatas")
    status_id: Mapped[int] = mapped_column(ForeignKey("status.id", ondelete="SET NULL"), nullable=True)

    name: Mapped["Name"] = relationship("Name", back_populates="raw_data")
    attachment_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    __table_args__ = (Index('ix_data_path_ops',
                            'metadata_json',
                            postgresql_using='gin', postgresql_ops={'data': 'jsonb_path_ops'}),)

    def __str__(self):
        return str(self.name_id) or ""

    def __repr__(self):
        return f"<Product(name='{self.name_id}', meta={self.metadata_json})>"


class Image(Base, BaseAt, ImageMixin):
    __table_args__ = (UniqueConstraint('image_id', 'name_id', name='uq_parser_images_unique'),)
    name_id: Mapped[int] = mapped_column(ForeignKey("names.id", ondelete="CASCADE"))
    name: Mapped["Name"] = relationship("Name", back_populates="images")

    def __str__(self):
        return self.name or ""


class Status(Base, BaseAt):
    status: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    # Relationships
    codes: Mapped[List["Code"]] = relationship("Code", back_populates="status")
    names: Mapped[List["Name"]] = relationship("Name", back_populates="status")
    rawdatas: Mapped[List["Rawdata"]] = relationship("Rawdata", back_populates="status")
    registry: Mapped[List["Registry"]] = relationship("Registry", back_populates="status")

    def __str__(self):
        return self.status or ""


class TaskLog(Base):
    """
    сохранение результатов arq
    """
    task_name: Mapped[str] = mapped_column(String(255), index=True)
    task_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)  # arq job_id
    status: Mapped[str] = mapped_column(String(50))  # started, success, failed
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, index=True)  # например, name_id
    error: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_requested: Mapped[bool] = mapped_column(default=False)

    def __str__(self):
        return self.task_name or ""
