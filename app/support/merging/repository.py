# app.support.merging.repository.py
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.support.drink.repository import DrinkRepository


class MergingRepository(DrinkRepository):

    @classmethod
    def get_distill_query(cls) -> Select:
        return select(cls.model)

    @classmethod
    def get_drinks_by_ids(cls, ids: list, session: AsyncSession):
        stmt = cls.get_distill_query().where(cls.model.id.in_(ids)).order_by(cls.model.id.asc())
        return cls.nonpagination(stmt, session)