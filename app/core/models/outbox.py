"""
Transactional outbox model for Meilisearch synchronization
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.sql import func
from app.core.models.base_model import Base


class Outbox(Base):
    """
    Outbox table to store changes that need to be synchronized with Meilisearch
    """
    __tablename__ = "outbox"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False, index=True)  # e.g., 'item', 'drink'
    entity_id = Column(Integer, nullable=False, index=True)  # ID of the entity
    operation = Column(String(20), nullable=False)  # 'INSERT', 'UPDATE', 'DELETE'
    payload = Column(Text)  # JSON payload of the entity data
    processed = Column(Boolean, default=False, index=True)  # Whether the sync task was processed
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)  # Error details if processing failed

    def __repr__(self):
        return f"<Outbox(id={self.id}, entity_type='{self.entity_type}', entity_id={self.entity_id}, operation='{self.operation}', processed={self.processed})>"