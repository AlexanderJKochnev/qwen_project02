# app.support.subregion.service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.services.service import Service
from app.support.country.repository import CountryRepository
from app.support.country.service import CountryService
from app.support.subregion.schemas import SubregionCreate, SubregionCreateRelation, SubregionRead
from app.support.region.repository import RegionRepository
from app.support.region.service import RegionService
from app.support.subregion.repository import SubregionRepository
from app.support import Region, Subregion


class SubregionService(Service):
    default: list = ['name', 'region_id']

    @classmethod
    async def create_relation(cls, data: SubregionCreateRelation, repository: SubregionRepository,
                              model: Subregion, session: AsyncSession, **kwargs) -> SubregionRead:
        kwargs['parent'] = 'region'
        kwargs['parent_repo'] = RegionRepository
        kwargs['parent_model'] = Region
        kwargs['parent_service'] = RegionService
        return super().create_relation(data, repository, model, session, **kwargs)
