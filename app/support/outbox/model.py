# app/support/outbox/model.py

import enum
from sqlalchemy import Column, Integer, String, JSON, DateTime, Enum, func
from sqlalchemy.orm import DeclarativeBase


class OutboxStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    FAILED = "failed"


class OutboxAction(enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class Base(DeclarativeBase):
    pass


class MeiliOutbox(Base):
    __tablename__ = "meili_outbox"

    id = Column(Integer, primary_key=True)
    index_name = Column(String, nullable=False)
    action = Column(Enum(OutboxAction), nullable=False)
    record_id = Column(String, nullable=False)  # ID записи в Meilisearch
    payload = Column(JSON, nullable=True)       # Данные для индексации
    status = Column(Enum(OutboxStatus), default=OutboxStatus.PENDING)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
