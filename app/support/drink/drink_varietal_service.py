# app/support/drink/services/drink_varietal_service.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.support.drink.drink_varietal_repo import DrinkVarietalRepository


class DrinkVarietalService:
    repo = DrinkVarietalRepository

    @classmethod
    async def get_drink_varietals_str(cls, drink_id: int, session: AsyncSession) -> List[str]:
        drink = await cls.repo.get_drink_with_varietals(drink_id, session)
        if not drink:
            return []
        return [varietal.__str__() for varietal in drink.varietals]

    @classmethod
    async def get_varietal_drinks_str(cls, varietal_id: int, session: AsyncSession) -> List[str]:
        varietal = await cls.repo.get_varietal_with_drinks(varietal_id, session)
        if not varietal:
            return []
        return [drink.__str__() for drink in varietal.drinks]

    @classmethod
    async def link_varietal_to_drink(cls, drink_id: int, varietal_id: int, session: AsyncSession):
        return await cls.repo.add_varietal_to_drink(drink_id, varietal_id, session)

    @classmethod
    async def unlink_varietal_from_drink(cls, drink_id: int, varietal_id: int, session: AsyncSession):
        return await cls.repo.remove_varietal_from_drink(drink_id, varietal_id, session)

    @classmethod
    async def update_link_priority(cls, drink_id: int, varietal_id: int, session: AsyncSession):
        return await cls.repo.update_priority(drink_id, varietal_id, session)

    @classmethod
    async def set_drink_varietals(cls, drink_id: int, varietal_ids: List[int], session: AsyncSession):
        return await cls.repo.set_drink_varietals(drink_id, varietal_ids, session)
