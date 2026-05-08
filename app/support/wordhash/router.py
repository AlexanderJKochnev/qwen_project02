# app/support/wordhash/router.py
from fastapi import BackgroundTasks, Query, Depends
from app.core.routers.base import BaseRouter
from app.core.config.database.db_async import DatabaseManager
from app.support.wordhash.model import WordHash
from app.support.wordhash.repository import WordHashRepository
from app.support.wordhash.service import WordHashService, ClickHashService


class WordHashRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=WordHash,
            prefix="/wordhash",
        )
        self.repo = WordHashRepository
        self.service = WordHashService

    def setup_routes(self):
        self.router.add_api_route("/rebuild_hash", self.rebuild_wordhash,
                                  methods=["GET"], response_model=dict,
                                  openapi_extra={'x-request-schema': None})
        self.router.add_api_route("/click_hash",
                                  self.get_click_hash, methods=["GET"], response_model=dict,
                                  openapi_extra={'x-request-schema': None}
        )
        super().setup_routes()

    async def rebuild_wordhash(self, background_tasks: BackgroundTasks) -> dict:
        # Запускает полный пересчет всех хэшей в фоне
        await self.service.rebuild_all_hashes(background_tasks, DatabaseManager.session_maker)
        # await WordHashService._run_rebuild_stream(session_factory=session_factory, background_tasks=background_tasks)
        return {"status": "queued", "message": "Пересчет хэшей запущен"}

    async def get_click_hash(self, background_tasks: BackgroundTasks,
                             page: int = Query(1, ge=1),
                             page_size: int = Query(20, ge=1),
                             click_service: ClickHashService = Depends()):
        """ получение хэшей из clickhouse """
        limit = (page_size - 1) * page
        result: dict = await click_service.get(limit, page)
        # добавление в wordhash
        if result:
            response = await self.service.create_bulk(result.get('result'))
        result['result'] = response
        return result