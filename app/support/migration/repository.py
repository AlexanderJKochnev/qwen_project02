# app.support.migration.repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, null
from app.core.repositories.sqlalchemy_repository import Repository
from app.support.migration.model import Migration
from app.support import Site, Subregion


class MigrationRepository(Repository):
    model = Migration

    async def tier_one(self, session: AsyncSession):
        stmt1 = insert(Site).from_select(
            [Site.subregion_id, Site.name], select(Subregion.id, null())
        )
        result = await session.execute(stmt1)
        if not result:
            raise Exception('{custom error in MigrationRepository}')
        session.flush()
        return result
