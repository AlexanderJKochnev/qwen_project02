# app/support/wordhash/router.py
from app.core.routers.base import BaseRouter
from app.core.config.database.db_async import DatabaseManager
from app.support.wordhash.model import WordHash
from app.support.wordhash.repository import WordHashRepository
from app.support.wordhash.service import WordHashService


class BackgroundTasks:
    pass


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
                                  methods=["GET"], response_model=None,
                                  openapi_extra={'x-request-schema': None})
        super().setup_routes()

    async def rebuild_wordhash(self, background_tasks: BackgroundTasks):
        # Запускает полный пересчет всех хэшей в фоне
        await self.service.rebuild_all_hashes(background_tasks, DatabaseManager.session_maker)
        # await WordHashService._run_rebuild_stream(session_factory=session_factory, background_tasks=background_tasks)
        return {"status": "queued", "message": "Пересчет хэшей запущен"}
