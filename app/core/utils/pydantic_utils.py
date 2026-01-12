# app/core/utils/pydantic_utils.py
# from pydantic import create_model, BaseModel
from decimal import Decimal
from typing import List, Optional, Type, Union, Dict, Any

from pydantic import BaseModel, create_model
from sqlalchemy import Float, inspect, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql.type_api import TypeEngine
from app.core.schemas.base import PaginatedResponse, PyModel
from fastapi.routing import APIRoute
from app.service_registry import get_service as get_serv, get_repo as get_rep, get_pyschema as get_pyschem


def get_field_name(schema: Type[BaseModel]):
    """ возвращает все имена полей pydantic models """
    return list(schema.model_fields.keys())


def get_routers(app, method: str = None) -> List[APIRoute]:
    """  список роутеров, содержащих указанный метод """
    # prefix содердится в a.path
    exc_route = ('/', '/auth/token', '/wait')
    if method:
        return [a for a in app.routes
                if all((isinstance(a, APIRoute), a.path not in exc_route)) and all((hasattr(a, 'methods'),
                                                                                    method in a.methods))]
    else:
        return [a for a in app.routes
                if all((isinstance(a, APIRoute), a.path not in exc_route)) and hasattr(a, 'methods')]


def get_service(model: Union[Type[DeclarativeBase], str]):
    """
    получение service layer по имени
    :param model: модель / имя модели
    """
    if not isinstance(model, str):
        model = model.__name__
    return get_serv(model)
    # return ServiceMeta._registry.get(f'{model}'.lower(), None)


def get_repo(model: Union[Type[DeclarativeBase], str]):
    """
    получение репозитория по имени
    :param model: модель / имя модели
    """
    if not isinstance(model, str):
        model = model.__name__
    return get_rep(model)


def get_pyschema(model: Union[Type[DeclarativeBase], str], schema: str = 'Read') -> PyModel:
    """
        model: alchemy model or it's name
        получение pydantic schema по ее имени:
        name: имя схемы
        default: дефолтное имя (не у всех схем есть кастомизированные схемы, в этом случае берем базовую
    """
    if not isinstance(model, str):
        model = model.__name__
    result = get_pyschem(f'{model}{schema}'.lower())
    if not result:
        result = get_pyschem(f'{schema}'.lower())
    return result


def sqlalchemy_to_pydantic_post(
        model: Type[DeclarativeBase], *, exclude_fields: Optional[set] = None,
        optional_fields: Optional[set] = None, ) -> Type[BaseModel]:
    """
    Генерирует Pydantic модель для POST-запроса из SQLAlchemy 2+ модели.
    использование CategoryCreate = sqlalchemy_to_pydantic_post(Category)
    :param model: SQLAlchemy модель
    :param exclude_fields: Поля, которые нужно исключить (например, {'id', 'created_at'})
    :param optional_fields: Поля, которые должны быть Optional (даже если nullable=False)
    :return: Pydantic BaseModel класс
    """
    if exclude_fields is None:
        # Исключаем типичные служебные поля по умолчанию
        exclude_fields = {"id", "created_at", "updated_at"}

    if optional_fields is None:
        optional_fields = set()

    mapper = inspect(model)
    fields = {}

    for column in mapper.columns:
        if column.key in exclude_fields:
            continue

        # Определяем тип Python из типа SQLAlchemy
        python_type = _get_python_type(column.type)

        # Определяем, является ли поле обязательным
        is_required = not column.nullable and column.key not in optional_fields

        # Для Foreign Key - всегда int (ID связанной сущности)
        if hasattr(column, 'foreign_keys') and column.foreign_keys:
            python_type = int
            # Foreign Key обычно nullable=False, но может быть и nullable=True
            is_required = not column.nullable and column.key not in optional_fields

        # Если поле не обязательное - делаем его Optional
        if not is_required:
            from typing import Optional as TypingOptional
            python_type = TypingOptional[python_type]

        # Устанавливаем значение по умолчанию для необязательных полей
        default = ... if is_required else None

        fields[column.key] = (python_type, default)

    # Создаём Pydantic модель
    model_name = f"{model.__name__}Create"
    pydantic_model = create_model(model_name, **fields)

    return pydantic_model


def _get_python_type(sql_type: TypeEngine) -> type:
    """Преобразует SQLAlchemy тип в Python тип для Pydantic"""
    # Строковые типы
    if isinstance(sql_type, (String, Text)):
        return str

    # Целые числа
    if isinstance(sql_type, Integer):
        return int

    # Вещественные числа
    if isinstance(sql_type, Float):
        return float

    # Decimal (деньги, проценты и т.д.)
    if isinstance(sql_type, Numeric):
        return Decimal

    # По умолчанию - str (на случай неизвестных типов)
    return str


def make_paginated_response(items: List[Any], total: int,
                            page: int, page_size: int) -> Dict[str, Any]:
    """
        make paginated response based of PaginatedResponse & Read Schema
        see app.core.schemas.base.PaginatedResponse
        :return:  Dict[str, Any]
    """
    return {"items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "has_next": (page - 1) * page_size + len(items) < total,
            "has_prev": page > 1
            }


class PyUtils:

    @classmethod
    def read_response(cls, read_schema: Type[BaseModel]) -> Type[BaseModel]:
        return create_model(f'{read_schema.__name__}Response', __base__=read_schema)

    @classmethod
    def paginated_response(cls, schema: Type[BaseModel]) -> Type[BaseModel]:
        return create_model(f"Paginated{schema.__name__}",
                            items=(List[schema], ...),
                            total=(Optional[int], None),
                            page=(Optional[int], None),
                            page_size=(Optional[int], None),
                            has_next=(Optional[bool], None),
                            has_prev=(Optional[bool], None))

    @classmethod
    def non_paginated_response(cls, schema: Type[BaseModel]) -> Type[BaseModel]:
        return create_model(f'List{schema.__name__}',
                            items=(List[schema], ...))
