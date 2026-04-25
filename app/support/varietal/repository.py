# app/support/varietal/repository.py
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists
from sqlalchemy.orm import selectinload
from app.support.varietal.model import Varietal
from app.support.drink.model import DrinkVarietal, Drink
from app.support.item.model import Item
from app.core.exceptions import AppBaseException
from app.core.repositories.sqlalchemy_repository import Repository, ModelType


# VarietalRepository = RepositoryFactory.get_repository(Varietal)
class VarietalRepository(Repository):
    model = Varietal

    @classmethod
    def item_exists(cls, id: int):
        """
        good for update or delete
        """
        return exists().where(
            Drink.id == Item.drink_id,
            Drink.id == DrinkVarietal.drink_id,
            DrinkVarietal.varietal_id == id
        )

    @classmethod
    def get_query_back(cls, id: int):
        """ Returns a query to select Item IDs related to this model
             just for memory
        """
        return (select(Item.id)
                .join(Item.drink)
                .join(Drink.varietal_associations)
                .where(DrinkVarietal.varietal_id == id))

    @classmethod
    def get_query(cls, model: ModelType):
        # Добавляем загрузку связи с relationships
        return select(cls.model).options(selectinload(Varietal.drink_associations).joinedload(DrinkVarietal.drink))

    @classmethod
    async def get_by_ids(cls, ids: Tuple[int], model: ModelType, session: AsyncSession) -> Optional[ModelType]:
        """
            get records by ids tuple
        """
        stmt = select(model).where(model.id.in_(ids)).order_by(model.id.asc())
        # from sqlalchemy.dialects import postgresql
        # compiled_pg = stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True})
        # logger.error(compiled_pg)
        result = await cls.nonpagination(stmt, session)
        return result

    @classmethod
    async def get_full_with_pagination(
            cls, skip: int, limit: int, model: ModelType, session: AsyncSession, ) -> tuple:
        """
            Запрос полного списка с загрузкой связей и пагинацией
            return Tuple[List[instances], int]
        """
        try:
            stmt = select(model).order_by(model.id.asc())
            result = await cls.pagination(stmt, skip, limit, session)
            return result
        except Exception as e:
            raise AppBaseException(message=f'get_full_with_pagination.error; {str(e)}', status_code=404)
