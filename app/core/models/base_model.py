# app/core/models/base_model.py

from datetime import datetime, date
from decimal import Decimal
from typing import Annotated, Optional, Type, List
# from sqlalchemy.dialects.postgresql import MONEY
from sqlalchemy import DateTime, DECIMAL, func, text, Text, Computed, inspect, String, Index, Column
from sqlalchemy.dialects.postgresql import ARRAY, BIGINT
from sqlalchemy.dialects.postgresql import TSVECTOR
# from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column, ColumnProperty
# from app.core.config.project_config import settings

langs = ['en', 'ru', 'fr']

# 1. Primary Key (Autoincrement для int по умолчанию True)
int_pk = Annotated[int, mapped_column(primary_key=True)]

# 2. Datetime: server_default — это БД-шный NOW, а onupdate лучше тоже через func.now()
# created_at = Annotated[datetime, mapped_column(server_default=func.now())]
created_at = Annotated[datetime, mapped_column(DateTime(timezone=True), server_default=func.now())]

updated_at = Annotated[datetime, mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now(),  # Используем БД-функцию для консистентности
                                               index=True
                                               )]
"""
updated_at = Annotated[datetime, mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=datetime.now(timezone.utc),
                                               index=True)]
"""
# 3. Strings: В 2.0+ Mapped[str] по умолчанию nullable=False.
# Для уникальности и индексов:
str_uniq = Annotated[str, mapped_column(unique=True, index=True)]

# 4. Nullable Strings: Используй Optional[] или | None для корректной типизации
str_null_true = Annotated[Optional[str], mapped_column(nullable=True)]
str_null_index = Annotated[Optional[str], mapped_column(nullable=True, index=True)]
str_null_false = Annotated[str, mapped_column(nullable=False)]

# 5. Числа с дефолтом
nmbr = Annotated[int, mapped_column(server_default=text('0'))]

# 6. Text (Mapped[Optional[str]] укажет SQLAlchemy на тип TEXT/VARCHAR автоматически)
descr = Annotated[Optional[str], mapped_column(Text)]

# 7. Money & Decimals
money = Annotated[Optional[Decimal], mapped_column(DECIMAL(10, 2))]
volume = Annotated[Optional[Decimal], mapped_column(DECIMAL(5, 2))]
percent = Annotated[Optional[Decimal], mapped_column(DECIMAL(3, 2))]

# 8. Int or None
ion = Annotated[Optional[int], mapped_column()]

# 9. Boolean Triple (True, False, None)
boolnone = Annotated[Optional[bool], mapped_column()]


class Base(AsyncAttrs, DeclarativeBase):
    """ clear model with id only,
        common methods and properties, table name
    """
    __abstract__ = True
    # Кэш атрибутов для каждого класса (чтобы не вызывать inspect постоянно)
    _cached_cols = None
    _cached_rels = None

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
        if seen is None:
            seen = set()

        state = inspect(self)
        # 1. Защита от циклов. Используем identity (первичный ключ), если он есть
        obj_id = (self.__class__, state.identity or id(self))
        if obj_id in seen:
            return None
        seen.add(obj_id)

        cls = self.__class__
        if cls._cached_cols is None:
            cls._cached_cols = [c.key for c in state.mapper.column_attrs]
            cls._cached_rels = [r.key for r in state.mapper.relationships]

        result = {}
        loaded_data = state.dict

        # 2. Обработка колонок
        for key in cls._cached_cols:
            # ВАЖНО: используем getattr для колонок.
            # Для простых колонок (не связей) это безопасно в асинхронке,
            # так как они либо загружены, либо помечены как deferred.
            # Если поле в defer(), getattr вернет ошибку MissingGreenlet,
            # поэтому проверяем, загружено ли оно.
            if key in state.unloaded:
                continue

            value = getattr(self, key)
            if isinstance(value, (datetime, date)):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)
            else:
                result[key] = value

        # 3. Обработка связей (relationships)
        for key in cls._cached_rels:
            # Для связей проверка через .dict ОБЯЗАТЕЛЬНА,
            # чтобы не спровоцировать Lazy Load и ошибку Greenlet
            if key in loaded_data:
                value = loaded_data[key]
                if value is None:
                    result[key] = None
                elif isinstance(value, list):
                    result[key] = [item.to_dict(seen) if hasattr(item, 'to_dict') else item for item in value]
                elif hasattr(value, "to_dict"):
                    result[key] = value.to_dict(seen)

        return result

        """
        for key in self.__dict__.keys():
            if key.startswith("_"):
                continue
            value = getattr(self, key)
            if isinstance(value, list):
                # result[key] = [item.to_dict(seen) for item in value]
                result[key] = [item.to_dict(seen) if hasattr(item, 'to_dict') else item for item in value]
            elif hasattr(value, "__table__"):  # ORM-объект
                result[key] = value.to_dict(seen)
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, Decimal):
                result[key] = float(value)
            else:
                result[key] = value
        return result
        """

    def to_dict_fast(self, exclude=None, skip_empty=True):
        """
        Быстрая версия с пропуском пустых значений
        exclude - список полей которые должны быть исключены из вывода
        """
        if exclude is None:
            exclude = set()

        state = inspect(self)
        cls = self.__class__

        if not hasattr(cls, '_fast_cols'):
            cls._fast_cols = {'cols': [c.key for c in state.mapper.column_attrs],
                              'rels': [r.key for r in state.mapper.relationships]}

        result = {}
        loaded = state.dict

        # Колонки
        for key in cls._fast_cols['cols']:
            if key in exclude or key in state.unloaded:
                continue
            value = loaded.get(key)

            # Пропускаем пустые значения
            if skip_empty and value in (None, '', [], {}, set()):
                continue

            if value is not None:
                if isinstance(value, (datetime, date)):
                    result[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    result[key] = float(value)
                else:
                    result[key] = value
            elif not skip_empty:
                result[key] = None

        # Связи
        for key in cls._fast_cols['rels']:
            if key in exclude:
                continue

            # Проверяем наличие значения в loaded
            if key not in loaded:
                continue

            value = loaded[key]

            # Обработка None значения
            if value is None:
                if not skip_empty:
                    result[key] = None
                continue

            # Обработка списка объектов
            if isinstance(value, list):
                converted_list = []
                for item in value:
                    if hasattr(item, 'to_dict_fast'):
                        converted_item = item.to_dict_fast(exclude, skip_empty)
                        # Добавляем только если converted_item не пустой (при skip_empty=True)
                        if not skip_empty or converted_item:
                            converted_list.append(converted_item)
                    elif hasattr(item, 'to_dict'):
                        converted_item = item.to_dict()
                        if not skip_empty or converted_item:
                            converted_list.append(converted_item)
                    else:
                        # Если объект не имеет методов to_dict, пробуем преобразовать напрямую
                        if not skip_empty or item:
                            converted_list.append(item)

                # Добавляем результат, если список не пустой (при skip_empty=True)
                if not skip_empty or converted_list:
                    result[key] = converted_list

            # Обработка одиночного связанного объекта
            elif hasattr(value, 'to_dict_fast'):
                converted = value.to_dict_fast(exclude, skip_empty)
                if not skip_empty or converted:
                    result[key] = converted
            elif hasattr(value, 'to_dict'):
                converted = value.to_dict()
                if not skip_empty or converted:
                    result[key] = converted
            else:
                # Если объект не имеет методов to_dict, добавляем как есть
                if not skip_empty or value:
                    result[key] = value

        return result


class BaseAt:
    """ время создания/изменения записи """
    __abstract__ = True
    type_annotation_map = {datetime: DateTime(timezone=True), }
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
    name: Mapped[str_null_index]
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


class Hash:
    """ поле для HASH индексирования """
    __abstract__ = True
    hash: Mapped[int] = mapped_column(BIGINT, nullable=False, index=True)


class Search:
    """ поисковое поле для триграммного индекса """
    __abstract__ = True

    word_hashes: Mapped[List[int]] = mapped_column(ARRAY(BIGINT), nullable=True)

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


class FullTextSearchMixin:
    @declared_attr
    def __table_args__(cls):
        indexes = []

        for name, attr in cls.__dict__.items():
            if hasattr(attr, 'type') and isinstance(attr.type, (String, Text)):
                idx = Index(
                    f"ix_{cls.__tablename__}_{name}_lower_prefix", func.lower(attr)
                )
                indexes.append(idx)

        existing_args = getattr(cls, '__table_args__', None)
        if existing_args:
            if isinstance(existing_args, tuple):
                return existing_args + tuple(indexes)
            return (existing_args,) + tuple(indexes)

        return tuple(indexes) if indexes else None
