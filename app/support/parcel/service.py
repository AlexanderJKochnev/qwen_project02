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
    default: list = ['name']

    @classmethod
    async def create_relation(cls,
                              data: SiteCreateRelation,
                              repository: SiteRepository,
                              model: Site, session: AsyncSession,
                              **kwargs) -> SiteRead:
        # pydantic model -> dict
        data: dict = data.model_dump(exclude={'subregion'}, exclude_unset=True)
        if data.subregion:
            result, _ = await SubregionService.get_or_create(data.country, SubregionRepository, Subregion,
                                                             session)
            data['subregion_id'] = result.id
        site = SiteCreate(**data)
        result, _ = await cls.get_or_create(site, SiteRepository, Site, session)
        return result
