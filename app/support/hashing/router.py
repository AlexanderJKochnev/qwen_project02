# app/support/hashing/router.py
from app.core.routers.base import BaseRouter
from app.support import Item
from app.support.hashing.model import WordHash
from sqlalchemy.ext.asyncio import AsyncSession
# from app.core.config.database.db_async import get_db
from app.fill_wordhash import seed_word_dictionary


class HashingRouter(BaseRouter):
    def __init__(self):
        super().__init__(
            model=WordHash,
            prefix="/wordhash",
        )

    def setup_routes(self):
        super().setup_routes()
        # то что ниже удалить - было нужно до relation
        self.router.add_api_route(
            "/", self.goahed, methods=["GET"],
        )

    async def goahead(self, session: AsyncSession):
        nmbr = await seed_word_dictionary(session, Item, WordHash)
        return {f'{nmbr} records shall be added'}
