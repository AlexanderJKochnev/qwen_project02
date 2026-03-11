# app/support/producer/service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.service import Service
from app.support.producer.repository import ProducerRepository, ProducerTitleRepository
from app.support.producer.model import Producer, ProducerTitle
from app.support.producer.schemas import (ProducerTitleRead, ProducerRead, ProducerTitleUpdate, ProducerCreate,
                                          ProducerTitleCreate, ProducerCreateRelation)


class ProducerTitleService(Service):
    default: list = ['name']


class ProducerService(Service):
    default: list = ['name']

    @classmethod
    async def create_relation(cls,
                              data: ProducerCreateRelation,
                              repository: ProducerRepository,
                              model: Producer, session: AsyncSession,
                              **kwargs) -> ProducerRead:
        # pydantic model -> dict
        producer_data: dict = data.model_dump(exclude={'producertitle'}, exclude_unset=True)
        if data.producertitle:
            result, _ = await ProducerTitleService.get_or_create(data.country, ProducerTitleRepository, ProducerTitle,
                                                                 session)
            producer_data['producertitle_id'] = result.id
        region = ProducerCreate(**producer_data)
        result, _ = await cls.get_or_create(region, ProducerRepository, Producer, session)
        return result