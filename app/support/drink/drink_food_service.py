# app/support/drink/services/drink_food_service.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.support.drink.drink_food_repo import DrinkFoodRepository


class DrinkFoodService:
    repo = DrinkFoodRepository

    @classmethod
    async def get_drink_foods_str(cls, drink_id: int, session: AsyncSession) -> List[str]:
        drink = await cls.repo.get_drink_with_foods(drink_id, session)
        if not drink:
            return []
        return [food.__str__() for food in drink.foods]

    @classmethod
    async def get_food_drinks_str(cls, food_id: int, session: AsyncSession) -> List[str]:
        food = await cls.repo.get_food_with_drinks(food_id, session)
        if not food:
            return []
        return [drink.__str__() for drink in food.drinks]

    @classmethod
    async def link_food_to_drink(cls, drink_id: int, food_id: int,
                                 session: AsyncSession):
        return await cls.repo.add_food_to_drink(drink_id, food_id, session)

    @classmethod
    async def unlink_food_from_drink(cls, drink_id: int, food_id: int, session: AsyncSession):
        return await cls.repo.remove_food_from_drink(drink_id, food_id)

    @classmethod
    async def set_drink_foods(cls, drink_id: int, food_ids: List[int], session: AsyncSession):
        return await cls.repo.set_drink_foods(drink_id, food_ids, session)
