# app.support.region.service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.service import Service
from app.support.country.repository import CountryRepository
from app.support.country.service import CountryService
from app.support import Region, Country
from app.support.region.schemas import RegionCreateRelation, RegionRead
from app.support.region.repository import RegionRepository


class RegionService(Service):
    default: list = ['name', 'country_id']

    @classmethod
    async def create_relation(cls, data: RegionCreateRelation, repository: RegionRepository,
                              model: Region, session: AsyncSession, **kwargs) -> RegionRead:
        kwargs['parent'] = 'country'
        kwargs['parent_repo'] = CountryRepository
        kwargs['parent_model'] = Country
        kwargs['parent_service'] = CountryService
        return super().create_relation(data, repository, model, session, **kwargs)
