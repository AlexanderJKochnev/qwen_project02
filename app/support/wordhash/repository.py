# app/support/wordhash/repository.py
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.sqlalchemy_repository import Repository
from app.support import WordHash


class WordHashRepository(Repository):
    model = WordHash

    @classmethod
    async def get_all_words_stream(cls, session: AsyncSession):
        """Получает все слова через stream"""
        stmt = select(cls.model.word)
        stream_result = await session.stream(stmt)

        async for row in stream_result:
            yield row[0]

    @classmethod
    async def bulk_update_hashes(cls, session: AsyncSession, updates: list):
        """Массовое обновление хэшей"""
        if not updates:
            return

        chunk_size = 500
        for i in range(0, len(updates), chunk_size):
            chunk = updates[i:i + chunk_size]
            stmt = pg_insert(cls.model).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=['word'], set_={'hash': stmt.excluded.hash}
            )
            await session.execute(stmt)

        await session.flush()
