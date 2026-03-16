# app/support/producer/service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.service import Service
from app.support.producer.model import Producer, ProducerTitle
from app.support.producer.repository import ProducerRepository, ProducerTitleRepository
from app.support.producer.schemas import (ProducerCreateRelation, ProducerRead)


class ProducerTitleService(Service):
    default: list = ['name']


class ProducerService(Service):
    default: list = ['name', 'producertitle_id']

    @classmethod
    async def create_relation(cls, data: ProducerCreateRelation, repository: ProducerRepository,
                              model: Producer, session: AsyncSession, **kwargs) -> ProducerRead:
        kwargs['parent'] = 'producertitle'
        kwargs['parent_repo'] = ProducerTitleRepository
        kwargs['parent_model'] = ProducerTitle
        kwargs['parent_service'] = ProducerTitleService
        return super().create_relation(data, repository, model, session, **kwargs)
