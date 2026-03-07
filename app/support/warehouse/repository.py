# app/support/warehouse/repository.py

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.core.repositories.sqlalchemy_repository import ModelType, Repository
from app.support.warehouse.model import Warehouse


class WarehouseRepository(Repository):
    model = Warehouse

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(Warehouse).options(joinedload(Warehouse.customer))
