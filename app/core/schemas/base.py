# app/core/schemas/base.py
"""
Базовые Pydantic схемы для валидации данных (включают поля из app/core/models/base_model/Base
# CreateSchema - все поля кроме id и timestamp, обязательныен поля обязательные
# UpdateSchema - все поля кроме id и timestamp, обязательныен поля необязательные
# DeleteResponse -
ReadSchema - все поля кроме tiimestamp
FullSchema - все поля
PaginatedResponse - см ниже на базе ReadSchema
ListResponse - тоже что и Pagianted только без Pagianted
"""
from datetime import datetime
from typing import Generic, List, NewType, Optional, TypeVar
from app.service_registry import register_pyschema
from pydantic import BaseModel as BaseOrigin, ConfigDict

# from abc import ABC

# Глобальный реестр pydantic схем
# PYDANTIC_MODELS: Set[Type[BaseOrigin]] = set()


class BaseModel(BaseOrigin):
    """
         вводим метод для получения только обязательных полей и регистрацию моделей
    """
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True, extra='ignore')

    def __init_subclass__(cls, **kwargs):
        # Автоматическая регистрация всех не-абстрактных классов
        if not getattr(cls, '__abstract__', False):
            key = cls.__name__.lower()
            register_pyschema(key, cls)  # print(f"✅ Зарегистрирована схема: {cls.__name__} -> ключ: '{key}'")

    def get_required_structure(self, deep: bool = False) -> dict:
        """ Рекурсивно получает структуру только с обязательными полями
            deep = true - поиск во вложенных моделях
        """
        result = {}
        EXCLUDE_LIST = ['id', 'pk', 'uuid', 'uid']  # исключает счетчики
        for field_name, field_info in self.model_fields.items():
            if field_name in EXCLUDE_LIST:
                continue
            if field_info.is_required():
                value = getattr(self, field_name)
                if deep:
                    # Рекурсивная обработка вложенных моделей
                    if isinstance(value, BaseModel):
                        result[field_name] = self.get_required_structure(value)
                    else:
                        result[field_name] = value
        return result


PyModel = NewType("PyModel", BaseModel)
T = TypeVar("T")


class PkSchema(BaseModel):
    """ только счетчик """
    id: int


class DateSchema(BaseModel):
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UniqueSchema(BaseModel):
    """ только уникальные поля """
    name: str


class DescriptionSchema(BaseModel):
    """ добавлять поля описаний на других языках """
    description: Optional[str] = None
    description_ru: Optional[str] = None
    description_fr: Optional[str] = None


"""
class DescriptionExcludeSchema(BaseModel):
    # добавлять поля описаний на других языках DELETE

    description: Optional[str] = Field(exclude=True)
    description_ru: Optional[str] = Field(exclude=True)
    description_fr: Optional[str] = Field(exclude=True)
"""


class NameSchema(BaseModel):
    """ добавлять поля на других языках """
    name: Optional[str] = None
    name_ru: Optional[str] = None
    name_fr: Optional[str] = None


"""
class NameExcludeSchema(BaseModel):
    # добавлять поля на других языках
    name: Optional[str] = Field(exclude=True)
    name_ru: Optional[str] = Field(exclude=True)
    name_fr: Optional[str] = Field(exclude=True)

"""


class LangSchema(NameSchema, DescriptionSchema):
    pass


class CreateSchema(LangSchema):
    """
    остальные поля добавить через CustomCreateSchema
    """
    name: str


class CreateSchemaSub(LangSchema):
    """
    остальные поля добавить через CustomCreateSchema
    для моделй с составными индексами
    name is optional
    """


class CreateNoNameSchema(DescriptionSchema):
    pass


class UpdateSchema(LangSchema):
    """
    остальные поля добавить через CustomUpdateSchema
    """
    name: Optional[str] = None


class UpdateNoNameSchema(DescriptionSchema):
    pass


class ReadSchema(PkSchema, LangSchema):
    pass


class ReadApiSchema(NameSchema):
    pass


class ReadNoNameSchema(PkSchema, DescriptionSchema):
    pass


class FullSchema(ReadSchema, DateSchema):
    """
    образец - неиспользовать делать DrinkFullSchema(DrinkRead, LangSchema)
    """
    pass


class ListResponse(BaseModel, Generic[T]):
    """
    просто список instances без пагнинации
    использовать в endpoints - вместо Generic[T] подствлять <model>Read
    """
    items: List[T]


class CreateResponse(PkSchema, DateSchema):
    pass


class PaginatedResponse(BaseOrigin, Generic[T]):
    """
    использовать в endpoints - вместо Generic[T] подствлять <model>Read
    """
    items: List[T]
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    has_next: Optional[int] = None
    has_prev: Optional[int] = None


class DeleteResponse(BaseModel):
    success: bool
    deleted_count: int = 1
    message: str


class UpdateResponse(BaseModel):
    success: bool
    updated_id: int
    message: str
# ---------------------NEW VIEWS--------------------------


class ListView(PkSchema):
    """
        id, name
        может быть еще что-то добавить из общих полей?
    """
    name: str


class DetailView(PkSchema):
    """
    """
    name: str
    description: Optional[str] = None
