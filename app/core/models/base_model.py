# app/core/models/base_model.py

from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, Optional, Type
# from sqlalchemy.dialects.postgresql import MONEY
from sqlalchemy import DateTime, DECIMAL, func, Integer, text, Text, Computed
from sqlalchemy.dialects.postgresql import TSVECTOR

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column
# from app.core.config.project_config import settings

langs = ['en', 'ru', 'fr']

# primary key
int_pk = Annotated[int, mapped_column(Integer, primary_key=True, autoincrement=True)]

# datetime field with default value now()
created_at = Annotated[datetime, mapped_column(DateTime(timezone=True), server_default=func.now())]

# datetime field with default and update value now()
updated_at = Annotated[datetime, mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=datetime.now(timezone.utc),
                                               index=True)]

# unique non-null string field
str_uniq = Annotated[str, mapped_column(unique=True,
                                        nullable=False, index=True)]

# non-unique nullable string field
str_null_true = Annotated[str, mapped_column(nullable=True)]
str_null_index = Annotated[str, mapped_column(nullable=True, index=True)]
str_null_false = Annotated[str, mapped_column(nullable=False)]

# int field with default value 0
nmbr = Annotated[int, mapped_column(server_default=text('0'))]

# text field wouthout default value
descr = Annotated[str, mapped_column(Text, nullable=True)]

# money
money = Annotated[Decimal, mapped_column(DECIMAL(10, 2), nullable=True)]

# volume,
volume = Annotated[Decimal, mapped_column(DECIMAL(5, 2), nullable=True)]

# alc sugar percentage
percent = Annotated[Decimal, mapped_column(
    DECIMAL(3, 2),
    nullable=True
)]

# int or none
ion = Annotated[int, mapped_column(nullable=True)]

# boolean triple
boolnone = Annotated[bool | None, mapped_column(nullable=True)]


class Base(AsyncAttrs, DeclarativeBase):
    """ clear model with id only,
        common methods and properties, table name
    """
    __abstract__ = True

    id: Mapped[int_pk]

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """
        имя таблицы в бд - имя модели во множ числе по правилам англ языка
        """
        name = cls.__name__.lower()
        return plural(name)
        """
        if name.endswith('model'):
            name = name[0:-5]
        if not name.endswith('s'):
            if name.endswith('y'):
                name = f'{name[0:-1]}ies'
            else:
                name = f'{name}s'
        return name
        """

    def __str__(self):
        # переоопределять в особенных формах
        # or "" на всякий случай если обязательное поле вдруг окажется необязательным и пустым
        return self.name or ""

    def __repr__(self):
        # return f"<Category(name={self.name})>"
        return str(self)

    def to_dict(self, seen=None) -> dict:
        """
        преобразует sqlalchemy instance в словарь
        foreign filed with lazy load преобразует во вложенные словари любой губины
        """
        if seen is None:
            seen = set()
        if self is None:
            return None

        obj_id = f"{self.__class__.__name__}_{id(self)}"
        if obj_id in seen:
            return None  # защита от циклов
        seen.add(obj_id)

        result = {}
        for key in self.__dict__.keys():
            if key.startswith("_"):
                continue
            value = getattr(self, key)
            if isinstance(value, list):
                result[key] = [item.to_dict(seen) for item in value]
            elif hasattr(value, "__table__"):  # ORM-объект
                result[key] = value.to_dict(seen)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)
            else:
                result[key] = value
        return result


class BaseAt:
    """ время создания/изменения записи """
    __abstract__ = True
    created_at: Mapped[created_at]
    updated_at: Mapped[updated_at]


class BaseInt:
    """ общие поля для всех таблиц на англ. языке """
    __abstract__ = True
    name: Mapped[str_uniq]
    description: Mapped[descr]


class BaseIntFree:
    """ общие поля для всех таблиц на англ. языке """
    __abstract__ = True
    name: Mapped[str_null_true]
    description: Mapped[descr]


class BaseDescription:
    """ общие поля для всех таблиц на разных языках
        добавлять по мере необходимости
        <имя поля>_<2х значный код страны/языка>
    """
    __abstract__ = True
    description_ru: Mapped[descr]
    description_fr: Mapped[descr]
    description_es: Mapped[descr]
    description_it: Mapped[descr]
    description_de: Mapped[descr]
    description_zh: Mapped[descr]
    # description_xx: Mapped[descr]


class BaseLang(BaseDescription):
    """
    общие поля для всех таблиц на разных языках
    """
    __abstract__ = True
    name_ru: Mapped[str_null_true]
    name_fr: Mapped[str_null_true]
    name_es: Mapped[str_null_true]
    name_it: Mapped[str_null_true]
    name_de: Mapped[str_null_true]
    name_zh: Mapped[str_null_true]
    # name_xx: Mapped[str_null_true]


class BaseFull(Base, BaseInt, BaseAt, BaseLang):
    __abstract__ = True
    pass


class BaseFullFree(Base, BaseIntFree, BaseAt, BaseLang):
    """ модель без обязательных полей под составной индекс"""
    __abstract__ = True

    def __str__(self):
        # Проходим по списку суффиксов и возвращаем первое непустое значение
        for lang in langs:
            if val := getattr(self, f"name{lang}", None):
                return val
        return ""


class Search:
    """ поисковое поле для триграммного индекса """
    __abstract__ = True

    @declared_attr
    def search_content(cls) -> Mapped[Optional[str]]:
        return mapped_column(Text, deferred=True, nullable=True)

    @declared_attr
    def search_vector(cls):
        return mapped_column(TSVECTOR, Computed("to_tsvector('simple', coalesce(search_content, ''))", persisted=True))

    """
    __table_args__ = (Index(
        "idx_search_content_null_only",  # Название индекса
        "id",  # Колонка, которую индексируем
        postgresql_where=(search_content == None),  # Условие: только NULL
    ),)"""


def plural(single: str) -> str:
    """
    возвращает множественное число прописными буквами по правилам англ языка
    :param single:  single name
    :type name:     str
    :return:        plural name
    :rtype:         str
    """
    name = single.lower()
    if name.endswith('model'):
        name = name[0:-5]
    if not name.endswith('s'):
        if name.endswith('y'):
            name = f'{name[0:-1]}ies'
        else:
            name = f'{name}s'
    return name


def get_model_by_name(model_name: str) -> Type[Base]:
    """
        быстрый способ получить модель по имени
    """
    # registry._class_map содержит пары {'ИмяКласса': КлассМодели}
    # return Base.registry._class_map.get(model_name)
    for mapper in Base.registry.mappers:
        if mapper.class_.__name__ == model_name:
            return mapper.class_
    return None


def get_model_by_name_stable(model_name):
    """
       стабильный способ получить модель по имени
       если и когда get_model_by_name перестанет работать - использовать этот
    """
    # .mappers — это итератор по всем мапперам в реестре
    for mapper in Base.registry.mappers:
        if mapper.class_.__name__ == model_name:
            return mapper.class_
    return None
