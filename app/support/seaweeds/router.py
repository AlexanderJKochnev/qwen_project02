# app.core.support.seaweeds.router.py
from fastapi import Depends
from app.core.routers.base import LightRouter
from app.support.seaweeds.service import SeaweedsService
from app.core.config.database.seaweed_async import SeaweedFSManager, get_swfs
from app.dependencies import get_clickhouse_repository_factory, ClickHouseRepositoryFactory
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Response
"""
    create
    search
    get
    get_by_id
    delete
    update
"""


class SeaweedsRouterr(LightRouter):
    def __init__(self):
        super().__init__(prefix='/seaweeds')
        self.service = SeaweedsService()

    async def create_img(self, description: str, file: UploadFile = File(...)):
        content = await file.read()
        # return fid
        response: dict = await self.service.create_img(content, description)
        return response
