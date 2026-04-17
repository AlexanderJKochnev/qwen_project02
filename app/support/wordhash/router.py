# app/support/wordhash/router.py
from app.core.routers.base import BaseRouter
from app.support.wordhash.model import WordHash
from app.support.wordhash.repository import WordHashRepository
from app.support.wordhash.service import WordHashService


class WordHashRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=WordHash,
            prefix="/wordhash",
        )
        self.repo = WordHashRepository
        self.service = WordHashService
