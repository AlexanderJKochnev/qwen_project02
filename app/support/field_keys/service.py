# app/support/field_keys/service.py
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.support.field_keys.repository import FieldKeyRepository


class FieldKeyService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = FieldKeyRepository(session)

    async def get_or_create_field_key(self, short_name: str, full_name: str) -> Dict[str, Any]:
        """Get or create a field key and return its data"""
        field_key = await self.repo.get_or_create(short_name, full_name)
        return {
            "id": field_key.id,
            "short_name": field_key.short_name,
            "full_name": field_key.full_name,
            "frequency": field_key.frequency
        }
