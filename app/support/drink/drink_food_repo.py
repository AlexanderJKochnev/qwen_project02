# app/support/drink/drink_food_repo.py
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.support.drink.model import Drink, DrinkFood
from app.support.food.model import Food


class DrinkFoodRepository:

    @classmethod
    async def get_drink_with_foods(cls, drink_id: int, session: AsyncSession):
        result = await session.execute(
            select(Drink)
            .where(Drink.id == drink_id)
            .options(selectinload(Drink.food_associations).joinedload(DrinkFood.food))
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_food_with_drinks(cls, food_id: int, session: AsyncSession):
        result = await session.execute(
            select(Food)
            .where(Food.id == food_id)
            .options(selectinload(Food.drink_associations).joinedload(DrinkFood.drink))
        )
        return result.scalar_one_or_none()

    @classmethod
    async def add_food_to_drink(cls, drink_id: int, food_id: int, session: AsyncSession):
        association = DrinkFood(drink_id=drink_id, food_id=food_id)
        session.add(association)
        await session.commit()
        # await self.session.refresh()
        return association

    @classmethod
    async def remove_food_from_drink(cls, drink_id: int, food_id: int, session: AsyncSession) -> bool:
        try:
            stmt = select(DrinkFood).where(DrinkFood.drink_id == drink_id, DrinkFood.food_id == food_id)
            result = await session.execute(stmt)
            association = result.scalar_one_or_none()
            if association:
                await session.delete(association)
                await session.commit()
                return True
        except Exception:
            return False

    @classmethod
    async def set_drink_foods(cls, drink_id: int, food_ids: list[int], session: AsyncSession):
        """Полная замена связей (для update)"""
        # Удаляем старые - ORM Method
        # stmt = select(DrinkFood).where(DrinkFood.drink_id == drink_id).execution_options(yield_per=1000)
        # result = session.scalars(stmt).yield_per(100)
        # for obj in result:
        #     await session.delete(obj)
        # await session.commit()
        # Non-orm method альтернативный способ удаления записей - быстрее но не поддердивает ORM-логику
        try:
            await session.execute(delete(DrinkFood).where(DrinkFood.drink_id == drink_id))
            # Добавляем новые
            associations = [
                DrinkFood(drink_id=drink_id, food_id=food_id)
                for food_id in food_ids
            ]
            session.add_all(associations)
            await session.commit()
            return True
        except Exception as e:
            raise Exception(f'ошибка при выполнении метода DrinkFoodRepository.set_drink_foods. {e}')
