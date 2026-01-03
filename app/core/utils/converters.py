# app/core/utils/converters.py
import re
from copy import deepcopy
from typing import Any, Dict, List, Union
from app.core.utils.morphology import to_nominative
import ijson
from pydantic import ValidationError

from app.core.config.project_config import settings
from app.core.utils.io_utils import get_filepath_from_dir_by_name
from app.support.item.schemas import ItemCreateRelation
from app.support.drink.schemas import DrinkCreateRelation


def detect_json_structure(filename):
    """
    определяет где находятся нужные записи
    в корне или на 2 уровне
    """
    with open(filename, 'rb') as file:
        parser = ijson.parse(file)
        try:
            # Первое событие — обычно 'start_map' для корня
            prefix, event, value = next(parser)
            if event == 'start_map':
                # Следующее событие — либо ключ корня, либо конец
                prefix, event, value = next(parser)
                if event == 'map_key':
                    if value in ['items', 'item']:
                        return value
                    else:
                        # Это ключ корневого уровня, значит, словари на первом уровне
                        return ''
        except StopIteration:
            pass
    return None


def read_json_by_keys(filename: str):
    """
        парсит json файл по одному значению (экономия памяти)
    """
    # получает путь к файлу
    filepath = get_filepath_from_dir_by_name(filename)
    # определяет на какой уровне находятся данныt: {data или {items:{data
    path = detect_json_structure(filepath)
    if path is None:
        raise ValueError("Не удалось определить структуру JSON-файла")

    with open(filepath, 'rb') as file:
        # Итерируемся по парам (ключ, значение) на корневом уровне
        for n, (key, value) in enumerate(ijson.kvitems(file, path)):
            yield key, value


def read_convert_json(filename: str = 'data.json'):
    """
        парсит json файл по одному значению (экономия памяти)
    """
    # получает путь к файлу
    filepath = get_filepath_from_dir_by_name(filename)
    # определяет на какой уровне находятся данныt: {data или {items:{data
    path = detect_json_structure(filepath)
    if path is None:
        raise ValueError("Не удалось определить структуру JSON-файла")

    with open(filepath, 'rb') as file:
        # Итерируемся по парам (ключ, значение) на корневом уровне
        for n, (key, value) in enumerate(ijson.kvitems(file, path)):
            yield n, convert_custom(value)


def convert_custom(dict1: Dict[str, Any]) -> Dict[str, Any]:
    """
        Конвертирует словарь 1 в словарь 2 согласно заданным правилам.
        Валидирует pymodel = ItemCreateRelation(**item)
            back_item = pymodel.model_dump(exclude_unset=True)
            assert item == back_item
    """
    source = deepcopy(dict1)
    # fields: madeof, recommendation, age
    redundant_fields = settings.redundant
    # Конвертируемые поля (остальные поля имеют исходный формат){'vol': 'float', 'count': 'int', 'alc': 'float'}
    casted_fields: dict = settings.casted_fields
    # Поля верхнего уровня (остальные поля в drink ('vol', 'count', 'image_path', 'image_id', 'uid')
    first_level_fields: list = settings.first_level_fields
    language_key: dict = settings.language_key  # {english: en, ...}
    # delimiter
    delim = settings.RE_DELIMITER
    # result dict root level
    item_dict: dict = {}
    # second level dict
    drink_dict: dict = {}
    # 0. make root level dict
    item_dict.update(root_level(source, first_level_fields, casted_fields))
    # 1. make drink level with simple fields
    drink_dict.update(drink_level(source, casted_fields, language_key))
    # 2. country->region->subregion
    get_subregion(drink_dict, language_key, delim)
    # 3. subcategory->category
    get_subcategory(drink_dict, language_key, delim)
    # 4. pairing -> foods
    get_pairing(drink_dict, language_key, delim)
    # 5. varietals
    get_varietal(drink_dict, language_key)
    drink_dict = {key.lower(): val for key, val in drink_dict.items()}
    # 6. remove redundant fields
    remove_redundant(item_dict, redundant_fields)
    # 7.1. ваkидация drink_dict
    try:
        # 7.1. валидация drink_dict
        drink = DrinkCreateRelation.model_validate(drink_dict)
        drink_validated = drink.model_dump(exclude_unset=True)
        item_dict['drink'] = drink_validated
        item = ItemCreateRelation.model_validate(item_dict)
        return item.model_dump(exclude_unset=True)
    except ValidationError as exc:
        for error in exc.errors():
            print(f"  Место ошибки (loc): {error['loc']}")
            print(f"  Сообщение (msg): {error['msg']}")
            print(f"  Тип ошибки (type): {error['type']}")
            # input_value обычно присутствует в словаре ошибки
            if 'input_value' in error:
                print(f"  Некорректное значение (input_value): {error['input_value']}")
            print("-" * 20)
        assert False, 'ошибка валидации в методе'
    except Exception as e:
        print(f'convert_custom.error: {e}')


def remove_redundant(root_dict: dict, redundant_fields: list):
    try:
        for key in redundant_fields:
            _ = root_dict.pop(key, None)
        return True
    except Exception as e:
        print(f'remove_redundant.error: {e}')
        return False


def get_varietal(drink_dict: dict, language_key: dict) -> bool:
    try:
        tmp: dict = {}
        for lang in language_key.values():
            varietal = drink_dict.pop(f'varietal{lang}', None)
            if not varietal:    # если нет varietal in data
                return True
            err = f'1: {varietal}'
            varietal = parse_grapes(varietal)
            err = f'2: {varietal}'
            tmp[f'name{lang}'] = varietal
        """
            tmp = {"name": {"Pinot Noir": 42, "Meunier": 12, "Chardonnay": 40},
                   "name_ru": {"Каберне Совиньон": 91, "Мерло": 6, "Пти Вердо": 2, "Мальбек": 1}
            convert to:
            varietals = [{"varietal": {"name": "Pinot Noir", "name_ru": "Пино Нуар"},
                          "precentage": 42},
                          ...
                          ]
        """
        varietals = convert_varietals(tmp)
        drink_dict['varietals'] = varietals
        return True
    except Exception as e:
        print(f'get_varietal.error: {e}')
        print(f'{err=}')
        return False


def get_pairing(drink_dict: dict, language_key: dict,
                delim: str) -> bool:
    try:
        pair: dict = {}
        pair2: list = []
        for lang in language_key.values():
            # foods = dict_pop(drink_dict, f'pairing{lang}')
            foods = drink_dict.pop(f'pairing{lang}', None)
            if not foods:  # если нет pairing в исходных данных
                return True
            err = f'1: {foods=}'
            foods = split_outside_parentheses_multi(foods)
            err = f'2: {foods=}'
            if lang == '_ru':
                foods = [to_nominative(food) for food in foods]
            foods = [food.capitalize() if food else food for food in foods]
            err = f'3: {foods=}'
            if foods:
                pair[f'name{lang}'] = foods
            err = f'4: {pair=}'
        length = len(pair.get('name'))

        for n in range(length):
            item: dict = {"superfood": {"name": "Unclassified", "name_ru": "Не классифицированный"}}
            for key in pair.keys():
                val: list = pair[key]
                if val and len(val) < length:
                    val.extend([None] * (length - len(val)))
                item[key] = val[n]
            err = f'5: {item=}'
            pair2.append(item)
            err = f'6: {pair2=}'
        drink_dict['foods'] = pair2
        return True
    except Exception as e:
        print(f'get_pairing.error: {e}')
        print(err)
        return False


def country_norm(country: str, delim: str = '_') -> str:
    """ United_states_of_america -> United States Of America"""
    if not country:
        return country
    dlm = settings.RE_DELIMITER
    return (' ').join((item.capitalize().strip(dlm) for item in country.split("_")))


def get_subregion(drink_dict: dict, language_key: dict,
                  delim: str) -> bool:
    """
        формируем subregion->region->country
    """
    try:
        dlm = settings.RE_DELIMITER
        country = dict_pop(drink_dict, 'country')
        country = country_norm(country)
        subregion = {"region": {"country": {"name": country}}}
        for lang in language_key.values():
            tmp = dict_pop(drink_dict, f'region{lang}')
            region, sub = split_outside_parentheses(tmp, delim)
            subregion[f'name{lang}'] = sub.capitalize().strip(dlm) if sub else None
            subregion['region'][f'name{lang}'] = region.capitalize().strip(dlm) if region else None
        drink_dict['subregion'] = subregion
        return True
    except Exception as e:
        print(f'get_subregion.error: {e}')


def get_subcategory(drink_dict: dict, language_key: dict,
                    delim: str) -> bool:
    """
    формируем subcategory->category
    """
    try:
        delim = settings.RE_DELIMITER
        wine_category = settings.wine_category
        category = dict_pop(drink_dict, 'category')
        if category in wine_category:
            subcat, category = category.capitalize(), 'Wine'
            subcat = subcat.capitalize().strip(delim)
            subcategory = {"name": subcat, "category": {"name": category}}
        else:
            subcategory = {"category": {"name": category.capitalize()}}
            for lang in language_key.values():
                tmp = dict_pop(drink_dict, f'type{lang}')
                subcat = tmp.capitalize().strip(delim) if tmp else None
                subcategory[f'name{lang}'] = subcat
        drink_dict['subcategory'] = subcategory
        return True

    except Exception as e:
        print(f'get_category.error: {e}')
        return False


def split_outside_parentheses(text: str, separators=',.:;') -> List:
    """
    Разделяет строку по первому найденному разделителю (из списка ',.:;'),
    который находится **вне скобок** `()`.
    Возвращает список из двух частей (до и после разделителя).
    Если разделителей вне скобок нет — возвращает список с одной строкой
    (без изменений, но с удалёнными пробелами по краям) + None.
    """
    try:
        if not text:
            return [None, None]

        depth = 0  # уровень вложенности скобок
        for i, char in enumerate(text):
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                # Защита от отрицательной глубины (например, ")abc")
                if depth < 0:
                    depth = 0
            elif depth == 0 and char in separators:
                # Найден разделитель вне скобок
                left = text[:i].strip(f' {separators}:')
                right = text[i + 1:].strip(f' {separators}:')
                return [left, right]
        # Разделителей вне скобок не найдено
        return [text.strip(), None]
    except Exception as e:
        print(f'split_outside_parentheses.error: {e}. input_value: {text}')


def drink_level(source: dict, casted_fields: dict, language_key: dict) -> dict:
    result: dict = {}
    for key, val in source.items():
        if isinstance(val, dict):
            suffix = language_key[key]
            for k2, v2 in val.items():
                result[f'{k2}{suffix}'] = field_cast(k2, v2, casted_fields)
        else:
            result[key] = field_cast(key, val, casted_fields)
    return result


def root_level(source: dict, first_level_fields: tuple, casted_fields: dict) -> dict:
    """
        собирает словарь корневого уровня
    """
    newdict: dict = {}
    for val in first_level_fields:
        value = dict_find(source, val)
        if val in casted_fields.keys():
            value = field_cast(val, value, casted_fields)
            newdict[val] = value
        if val == 'uid':
            newdict['image_path'] = f'{dict_find(source, 'uid')}.png'
    return newdict


def field_cast(field_name: str, val: Any, casted_fields: dict) -> Union[float, int, str]:
    """
    преобразует значение в требуемый тип
    """
    try:
        casting = casted_fields.get(field_name)
        match casting:
            case 'float':
                result = string_to_float(val)
            case 'int':
                result = string_to_int(val)
            case _:
                result = val
        return result
    except Exception as e:
        print(f'field_cast.error: {e}')


def string_to_float(s: str) -> float:
    """
    Преобразует строку в float, удаляя все символы кроме цифр и точки,
    заменяя запятую на точку.
    """
    if not s:
        return 0.0
    if isinstance(s, float):
        return s
    # Заменяем запятую на точку
    s = s.replace(',', '.')

    # Оставляем только цифры и точки
    cleaned = ''.join(c for c in s if c.isdigit() or c == '.')

    # Удаляем лишние точки (оставляем только первую)
    parts = cleaned.split('.')
    if len(parts) > 1:
        cleaned = parts[0] + '.' + ''.join(parts[1:])

    try:
        return float(cleaned) if cleaned else 0.0
    except ValueError:
        return 0.0


def float_to_int(f: float) -> int:
    try:
        # float, округляем по математическим правилам, затем в int
        return int(round(f)) if f else 0
    except ValueError:
        return 0


def string_to_int(s: Any) -> int:
    if isinstance(s, int):
        return s
    return float_to_int(string_to_float(s))


def dict_find(d, key):
    """
    Ищет ключ в многоуровневом словаре и возвращает значение, если найден.
    Возвращает None, если ключ не найден.
    """
    if not isinstance(d, dict):
        return None

    if key in d:
        return d[key]

    for k, v in d.items():
        if isinstance(v, dict):
            result = dict_find(v, key)
            if result is not None:
                return result
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    result = dict_find(item, key)
                    if result is not None:
                        return result
    return None


def dict_pop(d, key):
    """
    Ищет и удаляет ключ в многоуровневом словаре, возвращает значение, если найден.
    Возвращает None, если ключ не найден.
    """
    if not isinstance(d, dict):
        return None

    if key in d:
        return d.pop(key)

    for k, v in d.items():
        if isinstance(v, dict):
            result = dict_pop(v, key)
            if result is not None:
                return result
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    result = dict_pop(item, key)
                    if result is not None:
                        return result
    return None


def split_outside_parentheses_multi(text: str, maxsplit: int = -1) -> list[str]:
    if not text:
        return []

    # Разделители-слова
    word_separators = settings.ext_delimiter  # ['and', 'or', 'и', 'или']
    # delim = settings.RE_DELIMITER
    word_pattern = r'\b(?:' + '|'.join(re.escape(w) for w in word_separators) + r')\b'

    # Компилируем регулярку для слов
    word_regex = re.compile(word_pattern, re.IGNORECASE)

    # Символы-разделители
    symbol_separators = set(',.:;')
    symbol_separators = set(settings.RE_DELIMITER)

    parts = []
    current = []
    depth = 0
    i = 0
    n = len(text)
    splits_done = 0

    while i < n:
        char = text[i]

        # Обработка скобок
        if char == '(':
            depth += 1
        elif char == ')':
            depth = max(0, depth - 1)

        # Проверка: находимся ли вне скобок
        if depth == 0:
            # Проверка на слово-разделитель
            match = word_regex.match(text, i)
            if match:
                sep_len = match.end() - match.start()
                # Нашли слово-разделитель
                if maxsplit < 0 or splits_done < maxsplit:
                    part = ''.join(current).strip()
                    if part:
                        parts.append(part)
                    current = []
                    splits_done += 1
                    i += sep_len
                    continue
            # Проверка на символ-разделитель
            elif char in symbol_separators:
                if maxsplit < 0 or splits_done < maxsplit:
                    part = ''.join(current).strip()
                    if part:
                        parts.append(part)
                    current = []
                    splits_done += 1
                    i += 1
                    continue

        # Добавляем символ в текущую часть
        current.append(char)
        i += 1

    # Добавляем последнюю часть
    last_part = ''.join(current).strip()
    if last_part:
        parts.append(last_part)

    return parts


def parse_grapes(text: str) -> dict[str, int]:
    if not text or not text.strip():
        return {}

    text = text.strip().rstrip('.')

    # Разделяем на компоненты
    parts = split_outside_parentheses_multi(text)

    items = []
    total_percent = 0
    has_percent = False

    for part in parts:
        part_orig = part.strip()
        if not part_orig:
            continue

        # === УДАЛЯЕМ КАВЫЧКИ ТОЛЬКО ПО КРАЯМ (до и после) ===
        quote_chars = '"«»“”‘’'
        part_clean = part_orig.strip(quote_chars + ' \t')

        # Ищем процент в конце (даже если были кавычки)
        # Паттерн: число, возможно диапазон, затем % в конце (с возможными пробелами)
        percent_match = re.search(r'(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?%$', part_clean)
        if percent_match:
            has_percent = True
            low = float(percent_match.group(1))
            high = float(percent_match.group(2)) if percent_match.group(2) else low
            percent = round((low + high) / 2)
            name_raw = part_clean[:percent_match.start()].rstrip()
            # Удаляем кавычки ещё раз, на случай, если они остались внутри
            name = name_raw.strip(quote_chars + ' \t')
            name = _normalize_grape_name(name)
            items.append((name, percent))
            total_percent += percent
        else:
            # Нет процента — сохраняем как есть (для равномерного деления)
            name = part_clean.strip(quote_chars + ' \t')
            name = _normalize_grape_name(name)
            items.append((name, None))

    # Обработка результатов
    if has_percent:
        return {name: p for name, p in items if p is not None}
    else:
        n = len(items)
        if n == 0:
            return {}
        base = 100 // n
        remainder = 100 % n
        return {
            name: base + (1 if i < remainder else 0)
            for i, (name, _) in enumerate(items)
        }


def _normalize_grape_name(name: str) -> str:
    if not name:
        return name
    # Убираем лишние пробелы
    name = re.sub(r'\s+', ' ', name.strip())
    # -----------
    name = name.replace('"', '')
    # -----------
    words = []
    for word in name.split():
        if len(word) == 0:
            continue
        # Если слово — скобка целиком, обрабатываем содержимое
        if word.startswith('(') and word.endswith(')') and len(word) > 2:
            inner = word[1:-1]
            inner_norm = ' '.join(w.capitalize() for w in inner.split())
            words.append(f"({inner_norm})")
        else:
            words.append(word.capitalize())
    return ' '.join(words)


def convert_varietals(data: dict) -> list[dict]:
    if not data or "name" not in data:
        return []

    name_dict = data["name"]
    if not name_dict:
        return []

    # Получаем все языковые ключи
    lang_keys = [k for k in data.keys() if isinstance(data[k], dict)]

    # Преобразуем каждый словарь в список значений (названий), в порядке keys
    name_items = list(name_dict.items())  # [(name_en, pct), ...]
    lang_lists = {}
    for lang in lang_keys:
        lang_dict = data[lang]
        lang_lists[lang] = list(lang_dict.keys())  # только названия (ключи)

    result = []
    n = len(name_items)

    for i in range(n):
        name_en, percentage = name_items[i]
        varietal_entry = {}
        for lang in lang_keys:
            lang_names = lang_lists[lang]
            if i < len(lang_names):
                varietal_entry[lang] = lang_names[i]
            else:
                varietal_entry[lang] = None
        result.append({
            "varietal": varietal_entry,
            "percentage": percentage
        })
    return result
