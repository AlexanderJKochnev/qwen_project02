# app.core.repositories.seaweed_repository.py
"""
    для совместимости - все методы уже есть в app.core.config.database.seaweed_async.py
"""
from fastapi import Depends
from app.core.config.database.seaweed_async import SeaweedFSManager, get_swfs


class SeaweedRepository:

    @classmethod
    async def create(cls, content: bytes, metadata: dict, sf: SeaweedFSManager, **kwargs):
        """
            1. запись в seaweed, получение fid
            2. запись в clickhouse
            3. возврат:
            {fid: str}
        """
        if content:
            fid = sf.upload(content)
