# app/support/subcategory/schemas.py

from typing import Optional

from pydantic import computed_field, Field

from app.core.schemas.base import (CreateResponse, CreateSchemaSub, ReadApiSchema, ReadSchema, UpdateSchema,
                                   DetailView, ListView)
from app.support.category.schemas import CategoryCreateRelation, CategoryRead


class CustomReadSchema:
    category: CategoryRead


class SubcategoryReadApiSchema(ReadApiSchema):
    category: ReadApiSchema = Field(exclude=True)

    def __get_lang__(self, lang: str = '_ru', ) -> str:
        schema, field_name = self.category, 'name'
        if schema:
            prefix = getattr(schema, f'{field_name}{lang}') or getattr(schema, f'{field_name}')
            return prefix
        return None

    @computed_field
    @property
# /workspace/app/support/subcategory/schemas.py ru start 0001
    def category_ru(self) -> str:
# /workspace/app/support/subcategory/schemas.py ru end 0001
        return self.__get_lang__('_ru')

    @computed_field
    @property
# /workspace/app/support/subcategory/schemas.py fr start 0001
    def category_fr(self) -> str:
# /workspace/app/support/subcategory/schemas.py fr end 0001
        return self.__get_lang__('_fr')

    @computed_field
    @property
    def category_en(self) -> str:
        return self.__get_lang__('')


class CustomCreateSchema:
    category_id: int


class CustomCreateRelation:
    category: CategoryCreateRelation


class CustomUpdSchema:
    # category: Optional[CategoryCreateRelation]
    category_id: Optional[int] = None


class SubcategoryRead(ReadSchema, CustomReadSchema):
    pass


class SubcategoryReadRelation(SubcategoryRead):
    pass


class SubcategoryCreateRelation(CreateSchemaSub, CustomCreateRelation):
    pass


class SubcategoryCreate(CreateSchemaSub, CustomCreateSchema):
    pass


class SubcategoryUpdate(UpdateSchema, CustomUpdSchema):
    pass


class SubcategoryCreateResponseSchema(SubcategoryCreate, CreateResponse):
    pass


class SubcategoryDetailView(DetailView):
    category: Optional[CategoryRead] = None


class SubcategoryListView(ListView):
    # country: Optional[ListView] = None
    pass