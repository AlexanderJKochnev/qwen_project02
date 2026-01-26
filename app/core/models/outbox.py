# app/core/models/outbox.py

"""
Transactional outbox model for Meilisearch synchronization
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, and_
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

    @classmethod
    def get_unprocessed_entries(cls, entity_type: str = None, limit: int = 100):
        """Get unprocessed outbox entries with optional filtering by entity type"""
        from sqlalchemy import select
        query = select(cls).where(cls.processed.is_(False))
        if entity_type:
            query = query.where(cls.entity_type == entity_type)
        query = query.limit(limit)
        return query

    @classmethod
    def mark_as_processed(cls, entry_ids: list):
        """Mark multiple entries as processed"""
        from sqlalchemy import update
        return update(cls).where(cls.id.in_(entry_ids)).values(
            processed=True, 
            processed_at=func.now()
        )

    @classmethod
    def mark_as_failed(cls, entry_id: int, error_msg: str):
        """Mark an entry as failed with error message"""
        from sqlalchemy import update
        return update(cls).where(cls.id == entry_id).values(
            processed=True,
            processed_at=func.now(),
            error_message=error_msg
        )
