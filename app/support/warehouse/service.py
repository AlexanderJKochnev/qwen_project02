# app.support.warehouse.service.py
from app.core.services.service import Service
from sqlalchemy.ext.asyncio import AsyncSession
from app.support.warehouse.model import Warehouse
from app.support.warehouse.schemas import WarehouseCreate, WarehouseCreateRelation, WarehouseRead
from app.support.warehouse.repository import WarehouseRepository
from app.support.customer.model import Customer
from app.support.customer.repository import CustomerRepository
from app.support.customer.service import CustomerService


class WarehouseService(Service):

    @classmethod
    async def create_relation(cls, data: WarehouseCreateRelation, repository: WarehouseRepository,
                              model: Warehouse, session: AsyncSession) -> WarehouseRead:
        # pydantic model -> dict
        warehouse_data: dict = data.model_dump(exclude={'customer'}, exclude_unset=True)
        if data.customer:
            result, _ = await CustomerService.get_or_create(data.customer, CustomerRepository, Customer, session)
            warehouse_data['customer_id'] = result.id
        warehouse = WarehouseCreate(**warehouse_data)
        result, _ = await WarehouseService.get_or_create(warehouse, WarehouseRepository, Warehouse, session)
        return result
