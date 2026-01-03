# app/support/field_keys/repository.py
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.support.field_keys.model import FieldKey


class FieldKeyRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_full_name(self, full_name: str) -> Optional[FieldKey]:
        """Get a field key by its full name"""
        query = select(FieldKey).where(FieldKey.full_name == full_name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, short_name: str, full_name: str) -> FieldKey:
        """Create a new field key"""
        field_key = FieldKey(short_name=short_name, full_name=full_name, frequency=1)
        self.session.add(field_key)
        await self.session.commit()
        await self.session.refresh(field_key)
        return field_key

    async def increment_frequency(self, field_key: FieldKey) -> FieldKey:
        """Increment the frequency of a field key"""
        field_key.frequency += 1
        await self.session.commit()
        await self.session.refresh(field_key)
        return field_key

    async def get_or_create(self, short_name: str, full_name: str) -> FieldKey:
        """Get a field key by full name or create it if it doesn't exist"""
        field_key = await self.get_by_full_name(full_name)
        if field_key:
            return await self.increment_frequency(field_key)
        else:
            return await self.create(short_name, full_name)
