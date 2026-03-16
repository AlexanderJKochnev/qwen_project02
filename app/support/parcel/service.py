# app.support.parcel.service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.service import Service
from app.support.parcel.repository import SiteRepository, ParcelRepository  # noqa: F401
from app.support.subregion.service import SubregionService
from app.support.subregion.repository import SubregionRepository
from app.support.subregion.model import Subregion
from app.support.parcel.model import Site
from app.support.parcel.schemas import (SiteCreate, SiteCreateRelation, SiteRead)


class ParcelService(Service):
    default: list = ['name']


class SiteService(Service):
    default: list = ['name', 'subregion_id']

    @classmethod
    async def create_relation(cls, data: SiteCreateRelation, repository: SiteRepository,
                              model: Site, session: AsyncSession, **kwargs) -> SiteRead:
        kwargs['parent'] = 'subregion'
        kwargs['parent_repo'] = SubregionRepository
        kwargs['parent_model'] = Subregion
        kwargs['parent_service'] = SubregionService
        return super().create_relation(data, repository, model, session, **kwargs)
