# app.support.seaweeds.service.py
"""
    create
    search
    get
    get_by_id
    delete
    update
"""
from fastapi import Depends
from app.core.services.service import Service
from app.core.config.database.seaweed_async import SeaweedFSManager, get_swfs
from app.dependencies import ClickHouseRepositoryFactory, get_clickhouse_repository_factory
from app.core.config.database.seaweed_async import get_swfs


class SeaweedsService:
    def __init__(self, fs: SeaweedFSManager = Depends(get_swfs),
                 click_repo_factory: ClickHouseRepositoryFactory=Depends(get_clickhouse_repository_factory),
                 ):
        self.click_repo = click_repo_factory.for_table('images_metadata')
        self.fs = fs

    async def create_img(self, content, description):


        fid = await self.fs.upload(content)
        return {"fid": fid, "url": await self.fs.get_public_url(fid)}
