# app.core.repositories.seaweed_repository.py
"""
    для совместимости - все методы уже есть в app.core.config.database.seaweed_async.py
"""
from app.core.config.database.seaweed_async import SeaweedFSManager


class SeaweedRepository:
    """
        получение списков не предусмотрено - это см clickhouse
    """

    @classmethod
    async def create(cls, content: bytes, sf: SeaweedFSManager, **kwargs) -> str:
        """
            1. запись в seaweed, получение fid
            3. возврат: fid: str
        """
        fid = await sf.upload(content)
        return fid

    @classmethod
    async def delete(cls, fid: str, sf: SeaweedFSManager, **kwargs) -> bool:
        await sf.delete(fid)
        return True

    @classmethod
    async def get_by_fid(cls, fid: str, sf: SeaweedFSManager, **kwargs) -> bytes:
        return await sf.download(fid)

    @classmethod
    async def update(cls, fid: str, content: bytes, sf: SeaweedFSManager, **kwargs) -> str:
        """
            update не существует в seaweed,
            поэтому вот так как ниже
        """
        new_fid = await sf.upload(content)
        await sf.delete(fid)
        return new_fid
