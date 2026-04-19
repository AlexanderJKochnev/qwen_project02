# app/support/wordhash/router.py
from app.core.routers.base import BaseRouter
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
        super().setup_routes()
        # то что ниже удалить - было нужно до relation
        self.router.add_api_route("/rebuildhash", self.rebuild_wordhash,
                                  methods=["GET"],
                                  openapi_extra={'x-request-schema': None})

    async def rebuild_wordhash(
            background_tasks: BackgroundTasks,
            # session_factory=Depends(get_db)
    ):
        """Запускает полный пересчет всех хэшей в фоне"""
        await WordHashService.rebuild_all_hashes(
            # session_factory=session_factory,
            background_tasks=background_tasks
        )
        return {"status": "queued", "message": "Пересчет хэшей запущен"}
