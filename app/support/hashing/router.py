# app/support/hashing/router.py
from app.core.routers.base import BaseRouter
from app.support.hashing.model import WordHash


class HashingRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=WordHash,
            prefix="/wordhash",
        )
