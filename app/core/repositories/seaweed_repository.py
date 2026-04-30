# app.core.repositories.seaweed_repository.py
"""
    для совместимости - все методы уже есть в app.core.config.database.seaweed_async.py
"""
from loguru import logger
from app.core.config.database.seaweed_async import SeaweedFSManager
from app.core.exceptions import AppBaseException


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
        if content:
            fid = await sf.upload(content)
            return fid
        else:
            raise AppBaseException(message='no content for upload', status_code=404)

    @classmethod
    async def delete(cls, fid: str, sf: SeaweedFSManager, **kwargs) -> bool:
        try:
            await sf.delete(fid)
            return True
        except Exception as e:
            logger.error(f'sf.delete. {e}')

    @classmethod
    async def get_by_fid(cls, fid: str, sf: SeaweedFSManager, **kwargs) -> bytes:
        try:
            return await sf.download(fid)
        except Exception as e:
            raise AppBaseException(message=f'sf.get_by_fid. {e}', status_code=500)

    @classmethod
    async def update(cls, fid: str, content: bytes, sf: SeaweedFSManager, **kwargs) -> str:
        """
            update не существует в seaweed,
            поэтому вот так как ниже
        """
        try:
            new_fid = await sf.upload(content)
            sf.delete(fid)
            return new_fid
        except Exception as e:
            raise AppBaseException(message=f'sf.update. {e}')
