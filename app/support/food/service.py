# app.support.food.service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Type
from app.core.services.service import Service
from app.support.superfood.model import Superfood
from app.support.superfood.repository import SuperfoodRepository
from app.support.superfood.service import SuperfoodService
from app.support.food.model import Food
from app.support.food.repository import FoodRepository
from app.support.food.schemas import FoodCreate, FoodCreateRelation, FoodRead


class FoodService(Service):

    @classmethod
    async def create_relation(
            cls, data: FoodCreateRelation, repository: Type[FoodRepository], model: Type[Food],
            session: AsyncSession, **kwargs) -> FoodRead:
        # pydantic model -> dict
        food_data: dict = data.model_dump(exclude={'superfood'}, exclude_unset=True)
        if data.superfood:
            result, _ = await SuperfoodService.get_or_create(data.superfood, SuperfoodRepository, Superfood, session)
            food_data['superfood_id'] = result.id
        food = FoodCreate(**food_data)
        result, _ = await cls.get_or_create(food, FoodRepository, Food, session)
        return result
