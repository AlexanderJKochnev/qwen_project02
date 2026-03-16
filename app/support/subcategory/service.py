# app.support.subcategory.service.py
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.services.service import Service
from app.support.category.repository import CategoryRepository
from app.support.category.service import CategoryService
from app.support import Subcategory, Category
from app.support.subcategory.repository import SubcategoryRepository
from app.support.subcategory.schemas import SubcategoryCreateRelation, SubcategoryRead


class SubcategoryService(Service):
    default: list = ['name', 'category_id']

    @classmethod
    async def create_relation(cls, data: SubcategoryCreateRelation, repository: SubcategoryRepository,
                              model: Subcategory, session: AsyncSession, **kwargs) -> SubcategoryRead:
        kwargs['parent'] = 'category'
        kwargs['parent_repo'] = CategoryRepository
        kwargs['parent_model'] = Category
        kwargs['parent_service'] = CategoryService
        return super().create_relation(data, repository, model, session, **kwargs)
