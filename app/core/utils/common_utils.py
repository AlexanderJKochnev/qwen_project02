# app/core/common_utils.py
# some useful utilits

from datetime import datetime, timezone
from fastapi import HTTPException
from typing import Any, Dict, List, Optional, Set, TypeVar, Union
import json
import re
# from sqlalchemy.sql.sqltypes import String, Text, Boolean
from sqlalchemy import Boolean, inspect, String, Text, Unicode, UnicodeText
from sqlalchemy.dialects.postgresql import CITEXT  # если используешь PostgreSQL
from sqlalchemy.orm import DeclarativeMeta, RelationshipProperty, selectinload
from sqlalchemy.sql.selectable import Select

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


def sort_strings_by_alphabet_and_length(strings: List[str]) -> List[str]:
    """
    Сортирует список строк сначала по алфавиту, затем по длине строки.

    Args:
        strings: Список строк для сортировки

    Returns:
        Отсортированный список строк
    """
    return sorted(strings, key=lambda s: (s.lower(), len(s)))


def get_searchable_fields(model: type) -> Dict[str, type]:
    """
    СЛОВАРЬ ПОЛЕЙ ПО КОТОРЫМ МОЖНО ОСУЩЕВЛЯТЬ ПОИСК
    Возвращает словарь: {field_name: field_type}
    включая:
    - простые поля модели
    - поля из relationships в формате: rel_name_field_name
    """
    mapper = model.__mapper__
    fields = {}

    # 1. Простые поля
    for column in mapper.columns:
        if column.primary_key or not hasattr(column.type, "python_type"):
            continue
        fields[column.name] = column.type.python_type

    # 2. Поля из relationships
    for rel_name, relationship in mapper.relationships.items():
        if relationship.uselist:  # one-to-many — ищем по связанным объектам
            continue  # пропускаем списки, ищем только many-to-one / one-to-one

        remote_model = relationship.entity.entity
        remote_mapper = remote_model.__mapper__

        for col in remote_mapper.columns:
            if col.primary_key:
                continue
            field_name = f"{rel_name}_{col.name}"
            fields[field_name] = col.type.python_type

    return fields


def apply_relationship_loads(stmt: Select, model: DeclarativeMeta) -> Select:
    """
    Автоматически добавляет .options(selectinload(...)) для всех many-to-one relationships.
    Используется при детальном чтении.
    """
    mapper = model.__mapper__
    for rel_name, relationship in mapper.relationships.items():
        if relationship.uselist:
            continue  # skip one-to-many (можно расширить при необходимости)
        stmt = stmt.options(selectinload(getattr(model, rel_name)))
    return stmt


def get_model_fields_info(model, schema_type: int = 0, include_list: list = []) -> dict:
    """
    Возвращает информацию о полях модели:
    - field_type: тип поля
    - nullable: может ли быть NULL (bool)
    - primary_key: является ли первичным ключом (bool)
    - foreign: является ли внешним ключом (bool)
    - has_default: есть ли значение по умолчанию (bool)
    - # default_value: само значение по умолчанию (если есть)
    schema_type:
    Read (0):   все поля кроме _id, pk, default_value
    Create (1): все поля кроме _id, pk, default_value, foreign
    Update (2): все поля кроме _id, pk, default_value, foreign | все поля optional
    include_list: имена полей которые должны быть включены обязательно
    """
    defval, pk, _id, foreign, updatable = False, False, False, True, True,
    match schema_type:
        case 0:  # Read
            pk, _id, defval, foreign = True, True, True, False
        case 1:  # Create
            pk, defval, foreign = True, True, False
        case 2:  # Update
            pk, defval, foreign, updatable = True, True, False, False
        case _:  # All
            pass

    fields_info = {}

    # 1. Стандартные колонки через __table__
    if hasattr(model, "__table__") and model.__table__ is not None:
        for col in model.__table__.columns:
            field_type = getattr(col.type, "python_type", None)
            if field_type is None:
                field_type = type(col.type)

            # Определяем наличие и значение по умолчанию
            has_default = False
            # default_value = None

            if col.default is not None:
                has_default = True
                # if col.default.is_scalar:
                #     default_value = col.default.arg
                # elif col.default.is_callable:
                #     default_value = f"<callable: {col.default.callable.__name__}>"
            elif col.server_default is not None:
                has_default = True
                # default_value = f"<server_default: {str(col.server_default)}>"
            # defval, pk, _id, foreign, updatable
            if all((pk, col.primary_key, col.name not in include_list)):
                continue
            if all((defval, has_default, col.name not in include_list)):
                continue
            if all((_id, col.name.endswith('_id'), col.name not in include_list)):
                continue
            xnullable = col.nullable if updatable else True
            fields_info[col.name] = {'field_type': field_type,
                                     'nullable': xnullable,
                                     'primary_key': col.primary_key,
                                     'foreign': False,  # Это не foreign key
                                     'has_default': has_default}  # , default_value)
    # 2. Relationships через маппер
    if all((hasattr(model, "__mapper__"), foreign)):
        for rel in model.__mapper__.relationships:
            direction = rel.direction.name
            target = rel.entity.class_  # .__name__
            # print(f'{target=}, {type(target)=}')
            if direction == "ONETOMANY":
                field_type = List[{target}]
                is_nullable = True
            else:  # MANYTOONE
                field_type = target
                is_nullable = True
                for local_col in rel.local_columns:
                    if hasattr(local_col, "nullable"):
                        is_nullable = local_col.nullable
                        break
            xnullable = is_nullable if updatable else True
            fields_info[rel.key] = {'field_type': field_type,
                                    'nullable': xnullable,
                                    'primary_key': False,
                                    'foreign': True,  # Это foreign key
                                    'has_default': False}  # , default_value)

    return fields_info


def print_model_schema(model, title=None):
    """
    Выводит схему модели в читаемом виде.
    """
    # schema = generate_model_schema(model)
    name = title or model.__name__
    print(f"\n📊 Схема модели: {name}")
    print("-" * 50)
    for field, info in model.items():
        type_str = info["type"]
        null_str = "NULL" if info["nullable"] else "NOT NULL"
        extra = ""
        if info.get("relation"):
            extra = f" 🔗 {info['direction']} → {info['back_populates']}"
        if info.get("default"):
            extra += f" (default={info['default']})"
        print(f"{field:20} : {type_str:12} | {null_str:8}{extra}")


def get_model_fields(model: ModelType, exclude_columns: List[str] = [],
                     list_view: bool = False,
                     detail_view: bool = False) -> List[str]:
    """ список полей модели отсортированный по типу и алфавиту"""
    mapper = inspect(model)
    columns = []

    # Группируем поля по категориям
    str_fields = []    # текстовые обязательные поля
    str_null_fields = []    # текстовые необязательные поля
    bool_fields = []
    rel_fields = []     # relation fields MANYTOONE (выпадающий список)
    back_fields = []     # relation fields ONETOMANY (List[str]?)
    many_fields = []     # relation fields MANYTOMANY (check boxes)
    memo_fields = []    # memo fields
    other_fields = []   # остальные поля
    other_null_fields = []

    for attr in mapper.attrs:
        if attr.key in exclude_columns:
            continue

        if isinstance(attr, RelationshipProperty):
            if attr.direction.name == "MANYTOONE":
                rel_fields.append(attr.key)
            elif attr.direction.name == "ONETOMANY":
                back_fields.append(attr.key)
            elif attr.direction.name == "MANYTOMANY":
                many_fields.append(attr.key)

            continue

        if hasattr(attr, "columns"):
            col = attr.columns[0]
            # Пропускаем поля с default
            if col.default is not None:  # or col.autoincrement:
                continue
            # Получаем тип поля
            col_type = col.type.__class__ if hasattr(col.type, '__class__') else type(col.type)
            if issubclass(col_type, Text):
                memo_fields.append(attr.key)
                continue
            if issubclass(col_type, Boolean):
                bool_fields.append(attr.key)
                continue
            if issubclass(col_type, String):
                if not col.nullable:
                    str_fields.append(attr.key)
                    continue
                str_null_fields.append(attr.key)
                continue
            # Другие типы (Integer и т.д.)
            if not col.nullable:
                other_fields.append(attr.key)
                continue
            other_null_fields.append(attr.key)
    """
    print(f'{str_fields=}')
    print(f'{str_null_fields=}')
    print(f'{bool_fields=}')
    print(f'{rel_fields=}')
    print(f'{other_fields=}')
    print(f'{other_null_fields=}')
    print(f'{memo_fields=}')
    """
    # Формируем итоговый порядок
    columns.extend(sort_strings_by_alphabet_and_length(str_fields))
    columns.extend(sort_strings_by_alphabet_and_length(str_null_fields))
    if not list_view:
        columns.extend(sort_strings_by_alphabet_and_length(other_fields))  # Добавляем другие типы после String
        columns.extend(sort_strings_by_alphabet_and_length(other_null_fields))
        columns.extend(sort_strings_by_alphabet_and_length(bool_fields))
        columns.extend(sort_strings_by_alphabet_and_length(rel_fields))
        columns.extend(sort_strings_by_alphabet_and_length(many_fields))
        columns.extend(sort_strings_by_alphabet_and_length(back_fields))
        columns.extend(sort_strings_by_alphabet_and_length(memo_fields))
    if detail_view:
        columns = [a for a in columns if all((not a.endswith('_id'), a != 'image_path'))]
    return columns


def get_text_model_fields(model: ModelType) -> List[str]:
    """
    получаем список имен текстовых полей модели
    :param model:  model
    :type model:   model type
    :return:       список имен текстовых поелй модели
    :rtype:        List[str]
    """
    # Список типов, которые считаем "текстовыми"
    text_types = (String, Text, Unicode, UnicodeText, CITEXT)
    return [col.name for col in model.__table__.columns if isinstance(col.type, text_types)]


def flatten_dict(
    d: Dict[str, Any],
    priority_fields: List[str],
    seen: Optional[Set[int]] = None,
    result: Optional[Dict[str, Any]] = None,
    parent_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Рекурсивно проходит по вложенному словарю и "поднимает" все словари,
    содержащие поля из priority_fields, как отдельные записи в плоском словаре.

    Пример:
        region: { name: "Catalonia", country: { name: "Spain" } }
        →
        { "region": "Catalonia", "country": "Spain" }

    :param d: исходный словарь
    :param priority_fields: приоритетные поля для извлечения значения (например, ['name', 'name_ru'])
    :param seen: защита от циклов
    :param result: аккумулятор результата
    :param parent_key: имя ключа на предыдущем уровне (для отладки/логики)
    :return: плоский словарь
    """
    if seen is None:
        seen = set()
    if result is None:
        result = {}

    obj_id = id(d)
    if obj_id in seen:
        return result
    seen.add(obj_id)

    for key, value in d.items():
        current_key = key  # Имя ключа, через которое доступен объект

        if isinstance(value, dict) and value:
            # Попробуем извлечь значение для этого словаря
            extracted = None
            for field in priority_fields:
                if field in value:
                    val = value[field]
                    if val not in [None, "", " ", []]:
                        extracted = val
                        break

            # Если извлекли — добавляем в результат по ключу `key`
            if extracted is not None:
                result[current_key] = extracted

            # Всё равно рекурсивно обходим вложенные структуры
            flatten_dict(value, priority_fields, seen, result, parent_key=current_key)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    flatten_dict(item, priority_fields, seen, result, parent_key=current_key)

        # Простые значения: оставляем в исходных ключах (но не перезаписываем, если уже есть)
        elif key not in result:  # чтобы не перебивать name-значения
            result[key] = value

    seen.discard(obj_id)
    return result


def json_flattern(self, data: dict, parent: str = '') -> dict:
    """ превращает словарь в плоский """
    result: dict = {}
    for key, val in data.items():
        if isinstance(val, dict):
            parent = f'{parent}.{key}'
            result.update(self.json_flattern(val, parent))
        else:
            result[f'{parent}.{key}'] = ', '.join(val) if isinstance(val, str) else val
    return result


def get_nested(d: dict, path: str) -> Any:
    """
    Получить значение из вложенного словаря по пути с точками.

    Пример:
        get_nested(data, 'subregion_id.region.country.name') -> 'Spain'
        get_nested(data, 'subregion_id.region.country') -> {'name': 'Spain', ...}

    Если ключ не найден — возвращает None.
    """
    keys = path.split('.')
    current: Any = d

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None  # Ключ не найден
    return current


def set_nested(d: dict, path: str, value: Any,
               create_missing: bool = True, replace_primitive: bool = True) -> None:
    """
    Установить значение вложенного словаря по вложенному пути с точками.
    Поддерживает:
      - создание промежуточных словарей (create_missing)
      - замену примитивов на словари (replace_primitive)
    Пример:
        d = {'a': 'string'}
        set_nested(d, 'a.b.c', 42, create_missing=True, replace_primitive=True)
        → d == {'a': {'b': {'c': 42}}}
    """
    keys = path.split('.')
    current = d
    parent = None
    parent_key = None

    for key in keys[:-1]:
        parent = current
        parent_key = key

        # Проверяем, что parent — словарь
        if not isinstance(parent, dict):
            if replace_primitive:
                # Заменяем примитив на словарь
                if isinstance(parent, dict) or parent is d:
                    # Это невозможно, логическая ошибка
                    pass
                raise TypeError(f"Parent is not a dict: {repr(parent)}")
            else:
                raise TypeError(f"Cannot access '{key}' — parent is not a dict: {repr(parent)}")

        if key in parent:
            current = parent[key]
            # Проверим, что current — словарь или можно создать
            if isinstance(current, dict):
                continue
            elif create_missing and replace_primitive:
                # Заменяем примитив на словарь
                parent[key] = {}
                current = parent[key]
            elif create_missing:
                raise TypeError(f"Cannot descend into '{key}' — value is {type(current).__name__}, not dict")
            else:
                raise KeyError(f"Key '{key}' exists but is not dict and create_missing=False")
        else:
            if create_missing:
                parent[key] = {}
                current = parent[key]
            else:
                raise KeyError(f"Key '{key}' not found and create_missing=False")

    # Теперь устанавливаем финальное значение
    final_key = keys[-1]

    if not isinstance(current, dict):
        if replace_primitive:
            # Заменяем текущий уровень (если он в словаре-родителе) на {}
            if isinstance(parent, dict) and parent_key is not None:
                parent[parent_key] = {}
                current = parent[parent_key]
            else:
                # current — это сам корень d, и он не dict
                if d is current and replace_primitive:
                    # Но d — аргумент функции, и мы не можем его переназначить
                    raise TypeError(
                        "Cannot replace root object if it's not a dict. Pass a dict as root."
                    )
                else:
                    raise TypeError(f"Cannot assign to '{final_key}' — parent is not a dict: {repr(current)}")
        else:
            raise TypeError(f"Cannot assign to '{final_key}' — parent is not a dict: {repr(current)}")

    current[final_key] = value


def get_all_dict_paths(data: Any, parent_path: str = "") -> dict:
    """ получает список сложных ключей словаря отсортированный по глубине вложенности по убыванию
    {
      "subregion_id.region.country": "country",
      "subregion_id.region", "region"},
      "foods[0]", "foods"},
      "foods[1]", "foods"},
      "foods[2]", "foods"},
      "varietals[0]", "varietals"},
      "varietals[1]", "varietals"},
      "varietals[2]", "varietals"},
      "category_id",  "category"},
      "color_id", "color"},
      "sweetness_id", "sweetness"},
      "subregion_id","subregion"}
    }
    """
    paths: list[str] = []

    if isinstance(data, dict):
        # Только если это НЕ корень, добавляем текущий путь
        # (корень — это сам data, и мы его не считаем "вложенным")
        if parent_path:
            paths.append(parent_path)

        for key, value in data.items():
            child_path = f"{parent_path}.{key}" if parent_path else key
            if isinstance(value, (dict, list)):
                paths.extend(get_all_dict_paths(value, child_path))

    elif isinstance(data, list):
        for idx, item in enumerate(data):
            list_path = f"{parent_path}[{idx}]"
            if isinstance(item, (dict, list)):
                paths.append(list_path)
                # Рекурсивно ищем внутри, но НЕ добавляем list_path повторно
                sub_paths = get_all_dict_paths(item, list_path)
                # Исключаем сам list_path из подпутей
                paths.extend(p for p in sub_paths if p != list_path)

    result = sorted(paths, key=lambda p: p.count('.') + p.count('['), reverse=True)
    return result
    return {x: x.split('.')[-1].replace('_id', '').split('[', 1)[0] for x in result}


def pop_nested(d: dict, path: str, default=None):
    keys = path.split('.')
    current = d
    for key in keys[:-1]:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    final_key = keys[-1]
    if isinstance(current, dict) and final_key in current:
        return current.pop(final_key)
    return default


def jprint(data: dict):
    """ красивая печать словарей, списков """
    print(json.dumps(data, indent=2, ensure_ascii=False))


def back_to_the_future(after_date: datetime) -> datetime:
    """ преобразует дату naive to time zone aware и проверяет не будущее ли это"""
    if after_date.tzinfo is None:
        after_date = after_date.replace(tzinfo=timezone.utc)
    if after_date > datetime.now(timezone.utc):  # datetime.utcnow():
        raise HTTPException(status_code=400, detail="Date cannot be in the future")
    return after_date


def enum_to_camel(input: str) -> str:
    if input:
        input = input.replace('_', ' ')
        return ' '.join((a.title() for a in input.split(' ')))
    else:
        return input


def camel_to_enum(input: str) -> str:
    if input:
        return input.lower().replace(' ', '_')
    else:
        return None


def clean_string(s: str) -> str:
    """
         очистка строки от битых экранированных скобок, служебных символов
    """
    if not isinstance(s, str):
        return s  # или raise ValueError, если нужно

    # Удаляем: скобки, кавычки, слэши, обратные слэши
    # Также заменяем управляющие символы на пробел или удаляем
    # Шаг 1: заменяем управляющие символы (\n, \r, \t и т.д.) на пробел
    s = re.sub(r'[\n\r\t\x00-\x1f\x7f]', ' ', s)

    # Шаг 2: удаляем нежелательные символы
    s = re.sub(r'[()\'"/\\»]', '', s)

    # Шаг 3 (опционально): сжать множественные пробелы в один и убрать по краям
    s = re.sub(r'\s+', ' ', s).strip()

    return s


def get_value(source: list, search: str) -> Union[list, str]:
    """
    как бы словарь - ищет второй элемент кортежа по имени первого. может вернуть список если
    первых элементов несколько
    :param source: [(key, val),(key, val),(key, val),...]
    :type source:  List[Tuple[str, str]]
    :param key: str
    :type key:  str
    :return:    val or tuple of val
    :rtype:     str | tuple
    """
    try:
        result = [val for key, val in source if key == search]
        return result if len(result) > 1 else result[0]
    except Exception:
        return None


def compare_dict_keys(dict1, dict2, path=""):
    """
    Сравнивает ключи двух вложенных словарей и возвращает разницу в ключах.
    Возвращает два списка:
    - added: ключи, которые есть в dict2, но нет в dict1 (путь +)
    - removed: ключи, которые есть в dict1, но нет в dict2 (путь -)
    """
    added = []
    removed = []

    # Собираем все пути до ключей в каждом словаре
    def get_all_paths(d, current_path=""):
        paths = set()
        if isinstance(d, dict):
            for key, value in d.items():
                new_path = f"{current_path}.{key}" if current_path else key
                paths.add(new_path)
                if isinstance(value, dict):
                    paths.update(get_all_paths(value, new_path))
                elif isinstance(value, list):
                    # Если значение — список, проверим его элементы на словари
                    for i, item in enumerate(value):
                        list_path = f"{new_path}[{i}]"
                        if isinstance(item, dict):
                            paths.update(get_all_paths(item, list_path))
        return paths

    paths1 = get_all_paths(dict1)
    paths2 = get_all_paths(dict2)

    added = sorted(paths2 - paths1)
    removed = sorted(paths1 - paths2)

    return added, removed


def compare_dicts(dict1, dict2, path="", differences=None):
    """
    Сравнивает ключи двух вложенных словарей и возвращает различия, если они есть

    Args:
        dict1: первый словарь
        dict2: второй словарь
        path: текущий путь в словаре (для вложенных структур)
        differences: список для накопления различий

    Returns:
        list: список различий в формате (путь, описание_различия)
    """
    if differences is None:
        differences = []

    # Получаем все уникальные ключи из обоих словарей
    all_keys = set(dict1.keys()) | set(dict2.keys())

    for key in sorted(all_keys):
        current_path = f"{path}.{key}" if path else key

        # Проверка наличия ключа
        if key not in dict1:
            differences.append((current_path, "key is absence in first dict"))
            continue
        elif key not in dict2:
            differences.append((current_path, "key is absence in second dict"))
            continue

        value1 = dict1[key]
        value2 = dict2[key]

        # Проверка типов
        type1 = type(value1)
        type2 = type(value2)

        if type1 != type2:
            differences.append((current_path, f"Несовпадение типов: {type1.__name__} - {type2.__name__}"))
            continue

        # Рекурсивное сравнение для вложенных словарей
        if isinstance(value1, dict) and isinstance(value2, dict):
            compare_dicts(value1, value2, current_path, differences)

        # Обработка списков
        elif isinstance(value1, list) and isinstance(value2, list):
            compare_lists(value1, value2, current_path, differences)
        # Для простых типов просто проверяем равенство  # (по заданию нужно только наличие ключей и типов)

    return differences


def compare_lists(list1, list2, path="", differences=None):
    """
    Сравнивает два списка (в контексте сравнения словарей)
    """
    if differences is None:
        differences = []

    # Проверяем длину списков
    if len(list1) != len(list2):
        differences.append((path, f"Разная длина списков: {len(list1)} - {len(list2)}"))

    # Сравниваем элементы списков (если они словари)
    for i, (item1, item2) in enumerate(zip(list1, list2)):
        item_path = f"{path}[{i}]"

        type1 = type(item1)
        type2 = type(item2)

        if type1 != type2:
            differences.append((item_path, f"Несовпадение типов в списке: {type1.__name__} - {type2.__name__}"))
        elif isinstance(item1, dict) and isinstance(item2, dict):
            compare_dicts(item1, item2, item_path, differences)


def print_comparison_results(dict1, dict2):
    """
    Сравнивает два словаря и выводит результаты в читаемом формате
    """
    print("=" * 60)
    print("СРАВНЕНИЕ ДВУХ СЛОВАРЕЙ")
    print("=" * 60)

    differences = compare_dicts(dict1, dict2)

    if not differences:
        print("✓ Словари идентичны по структуре и типам данных")
        return

    print("Найдены различия:")
    print("-" * 60)

    for path, description in differences:
        print(f"Путь: {path}")
        print(f"Описание: {description}")
        print("-" * 40)


def joiner(joint: str = '. ', *args) -> str:
    """
    объединяет элементы в строку убирая пустые (None) через разделитель
    :param args: List[Any]
    :type args:  list
    :return:     joined string
    :rtype:      str
    """
    return joint.join((val for val in args if val))


def dict_sorter(source: dict) -> dict:
    return dict(sorted(source.items(), key=lambda item: item[1]))


def flatten_dict_with_localized_fields(data: Dict[str, Any],
                                       fields: List[str],
                                       lang: str = 'en',
                                       reverse: bool = False) -> Dict[str, Any]:
    """
    принимает словарь с данными (schema.dump_to_dict()...
    списое полей
    и возвращает плоский словарь
    с полями только из fields,
    :param data:    словарь
    :type data:     dict
    :param fields:  имена полей которые должны войти в результат
    :type fields:   List[str]
    :param lang:    код языка (en, ru, fr, ...)
    :type lang:     str
    :param reverse:
    :type reverse:
    :return:
    :rtype:
    """
    if not fields:
        result = {'id': data['id']} if 'id' in data else {}
        return result

    # === 1. Извлекаем цепочку узлов от корня к самому глубокому уровню ===
    def get_nodes(node: Dict[str, Any]) -> List[Dict[str, Any]]:
        nodes = [node]
        for value in node.values():
            if isinstance(value, dict):
                nodes.extend(get_nodes(value))
                break
        return nodes

    all_nodes = get_nodes(data)
    ordered_nodes = list(reversed(all_nodes)) if not reverse else all_nodes

    result = {}
    if 'id' in data:
        result['id'] = data['id']

    main_field = fields[0]

    # === 2. Обработка ПЕРВОГО поля (рекурсивно, с объединением) ===
    def get_main_value(node: Dict[str, Any]) -> str | None:
        if lang != 'en':
            val = node.get(f"{main_field}_{lang}")
            if isinstance(val, str) and val != '':
                return val
        val = node.get(main_field)
        if isinstance(val, str) and val != '':
            return val
        return None

    main_parts = []
    for node in ordered_nodes:
        val = get_main_value(node)
        if val is not None:
            main_parts.append(val)
    if main_parts:
        result[main_field] = '. '.join(main_parts)

    # === 3. Обработка ОСТАЛЬНЫХ полей (только корень, без рекурсии) ===
    root = data
    for field in fields[1:]:
        # coalesce: field_lang → field
        if lang != 'en':
            val = root.get(f"{field}_{lang}")
            if isinstance(val, str) and val != '':
                result[field] = val
                continue
        val = root.get(field)
        # Даже если None или пусто — сохраняем как есть (в примере: 'description test')
        # Но по ТЗ: если coalesce дал непустое — берём, иначе?
        # В примере: 'description' = 'description test' → сохраняем
        if isinstance(val, str) and val != '':
            result[field] = val
        else:
            # Если хотим сохранять даже None/пустое — раскомментируйте:
            # result[field] = val
            # Но в примере вывода поле присутствует, значит — сохраняем любое значение из корня
            result[field] = val  # включая None, '', и т.д.

    return result


def coalesce(*args):
    for x in args:
        if x is not None:
            return x


def search_local(query_string: str) -> int:
    """
        определение языка текста
        1 -  русский (кириллица)
        2 - латиница
    """

    if re.search('[а-яА-Я]', query_string):
        return 1
    else:
        return 2


def localized_field_with_replacement(source: Dict[str, Any], key: str,
                                     langs: list, target_key: str = None) -> Dict[str, Any]:
    """
        source - словарь
        key: ключ
        langs: список языков
        target_key: имя поля (если None то key)
        1. Извлекает из словаря source значения key на всех языках
        2. Выбирает первое не пустое (langs - список suffixes языков отсортированных по приоритету)
        3. Возвращает словарь из одной пары target_key: val
    """
    for lang in langs:
        res = source.get(f'{key}{lang}')
        if res:
            return {target_key or key: res}
    else:
        return {target_key or key: None}
