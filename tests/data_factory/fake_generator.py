# tests/data_factory/fake_generator.py
# flake8: noqa: E501
import random
from decimal import Decimal
from random import randint
from typing import Any, Dict, get_args, get_origin, List, Optional, Type, Union

from faker import Faker
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel
from tests.data_factory.postprocessing import validate_and_fix_numeric_ranges


class TestDataGenerator:
    def __init__(self):
        self.fake_en = Faker('en_US')
        self.fake_ru = Faker('ru_RU')
        self.fake_fr = Faker('fr_FR')

        # Языковые фейкеры
        self.fakers = {
            'en': self.fake_en,
            'ru': self.fake_ru,
            'fr': self.fake_fr,
        }

        # Цвета на разных языках
        self.colors = {
            'en': ['Red', 'White', 'Rosé', 'Orange', 'Sparkling Red', 'Dessert Wine', 'Fortified'],
            'ru': ['Красное', 'Белое', 'Розовое', 'Оранжевое', 'Игристое красное', 'Десертное', 'Креплёное'],
            'fr': ['Rouge', 'Blanc', 'Rosé', 'Orange', 'Rouge mousseux', 'Vin de dessert', 'Fortifié'],
        }

        # Страны, регионы, субрегионы (упрощённый справочник)
        self.geo_hierarchy = [
            {
                'country': {'en': 'France', 'ru': 'Франция', 'fr': 'France'},
                'regions': [
                    {
                        'name': {'en': 'Bordeaux', 'ru': 'Бордо', 'fr': 'Bordeaux'},
                        'subregions': [
                            {'en': 'Médoc', 'ru': 'Медок', 'fr': 'Médoc'},
                            {'en': 'Saint-Émilion', 'ru': 'Сент-Эмильон', 'fr': 'Saint-Émilion'},
                            {'en': 'Pomerol', 'ru': 'Помроль', 'fr': 'Pomerol'},
                        ]
                    },
                    {
                        'name': {'en': 'Burgundy', 'ru': 'Бургундия', 'fr': 'Bourgogne'},
                        'subregions': [
                            {'en': 'Côte de Nuits', 'ru': 'Кот-де-Нюи', 'fr': 'Côte de Nuits'},
                            {'en': 'Côte de Beaune', 'ru': 'Кот-де-Бон', 'fr': 'Côte de Beaune'},
                        ]
                    },
                ]
            },
            {
                'country': {'en': 'Italy', 'ru': 'Италия', 'fr': 'Italie'},
                'regions': [
                    {
                        'name': {'en': 'Tuscany', 'ru': 'Тоскана', 'fr': 'Toscane'},
                        'subregions': [
                            {'en': 'Chianti', 'ru': 'Кьянти', 'fr': 'Chianti'},
                            {'en': 'Montalcino', 'ru': 'Монтальчино', 'fr': 'Montalcino'},
                        ]
                    },
                    {
                        'name': {'en': 'Piedmont', 'ru': 'Пьемонт', 'fr': 'Piémont'},
                        'subregions': [
                            {'en': 'Barolo', 'ru': 'Бароло', 'fr': 'Barolo'},
                            {'en': 'Asti', 'ru': 'Асти', 'fr': 'Asti'},
                        ]
                    },
                ]
            },
            {
                'country': {'en': 'Spain', 'ru': 'Испания', 'fr': 'Espagne'},
                'regions': [
                    {
                        'name': {'en': 'Rioja', 'ru': 'Рибера-дель-Дуэро', 'fr': 'Rioja'},
                        'subregions': [
                            {'en': 'Alavesa', 'ru': 'Алавеса', 'fr': 'Alavesa'},
                            {'en': 'Baja', 'ru': 'Баха', 'fr': 'Baja'},
                        ]
                    },
                ]
            },
        ]

    def _generate_string(self, key: str) -> str:
        lang = 'en'
        if key.endswith('_ru'):
            lang = 'ru'
        elif key.endswith('_fr'):
            lang = 'fr'

        faker = self.fakers[lang]

        if 'name' in key and 'description' not in key:
            return faker.word().capitalize()
        elif 'description' in key:
            return " ".join(faker.sentences(nb=random.randint(5, 10)))
        elif 'subtitle' == key:
            return faker.sentence(nb_words=6)
        else:
            return faker.sentence(nb_words=4)

    def _generate_decimal(self) -> float:
        return round(round(random.uniform(5.0, 16.0), 2))

    def _generate_integer(self) -> int:
        return random.randint(6, 36)

    def _generate_bool(self) -> bool:
        return random.choice([True, False])

    def _generate_color(self, key: str) -> str:
        lang = 'en'
        if key.endswith('_ru'):
            lang = 'ru'
        elif key.endswith('_fr'):
            lang = 'fr'
        return random.choice(self.colors[lang])

    def _generate_geo_data(self) -> Dict[str, Any]:
        country_data = random.choice(self.geo_hierarchy)
        region_data = random.choice(country_data['regions'])
        subregion_name = random.choice(region_data['subregions'])

        return {
            'country': {
                'name': country_data['country']['en'],
                'name_ru': country_data['country']['ru'],
                'name_fr': country_data['country']['fr'],
                'description': f"{country_data['country']['en']} is a country in Europe known for wine.",
                'description_ru': f"{country_data['country']['ru']} — страна в Европе, известная своими винами.",
                'description_fr': f"{country_data['country']['fr']} est un pays d'Europe réputé pour son vin.",
            },
            'region': {
                'name': region_data['name']['en'],
                'name_ru': region_data['name']['ru'],
                'name_fr': region_data['name']['fr'],
                'description': f"{region_data['name']['en']} is a wine region in {country_data['country']['en']}.",
                'description_ru': f"{region_data['name']['ru']} — винный регион в {country_data['country']['ru']}.",
                'description_fr': f"{region_data['name']['fr']} est une région viticole en {country_data['country']['fr']}.",
            },
            'subregion': {
                'name': subregion_name['en'],
                'name_ru': subregion_name['ru'],
                'name_fr': subregion_name['fr'],
                'description': f"{subregion_name['en']} is a subregion of {region_data['name']['en']}.",
                'description_ru': f"{subregion_name['ru']} — субрегион {region_data['name']['ru']}.",
                'description_fr': f"{subregion_name['fr']} est un sous-région de {region_data['name']['fr']}.",
            }
        }

    def _generate_list(self, template_list: List[Dict], depth: int = 0) -> List[Dict]:
        count = random.randint(1, 5)
        result = []
        for _ in range(count):
            item = self._generate_from_template(template_list[0], depth + 1)
            result.append(item)
        return result

    def _generate_from_template(self, template: Union[Dict, str], depth: int = 0) -> Any:
        if isinstance(template, str):
            # Примитивный тип
            if template == 'string':
                key = 'field'
                return self._generate_string(key)
            elif template == 'decimal':
                return self._generate_decimal()
            elif template == 'integer':
                return self._generate_integer()
            elif isinstance(template, bool):
                return self._generate_bool()
            else:
                return None

        if isinstance(template, dict):
            result = {}
            for key, value in template.items():
                if key == 'color_id':
                    # Специальная обработка цвета
                    result[key] = {
                        'name': self._generate_color('name'),
                        'name_ru': self._generate_color('name_ru'),
                        'name_fr': self._generate_color('name_fr'),
                        'description': self._generate_string('description'),
                        'description_ru': self._generate_string('description_ru'),
                        'description_fr': self._generate_string('description_fr'),
                    }
                elif key == 'subregion_id':
                    geo_data = self._generate_geo_data()
                    result[key] = {
                        'region': {
                            'country': geo_data['country'],
                            'name': geo_data['region']['name'],
                            'name_ru': geo_data['region']['name_ru'],
                            'name_fr': geo_data['region']['name_fr'],
                            'description': geo_data['region']['description'],
                            'description_ru': geo_data['region']['description_ru'],
                            'description_fr': geo_data['region']['description_fr'],
                        },
                        'name': geo_data['subregion']['name'],
                        'name_ru': geo_data['subregion']['name_ru'],
                        'name_fr': geo_data['subregion']['name_fr'],
                        'description': geo_data['subregion']['description'],
                        'description_ru': geo_data['subregion']['description_ru'],
                        'description_fr': geo_data['subregion']['description_fr'],
                    }
                elif key in ['category_id', 'sweetness_id']:
                    # Общие справочники
                    name = self._generate_string('name')
                    result[key] = {
                        'name': name,
                        'name_ru': self._generate_string('name_ru'),
                        'name_fr': self._generate_string('name_fr'),
                        'description': self._generate_string('description'),
                        'description_ru': self._generate_string('description_ru'),
                        'description_fr': self._generate_string('description_fr'),
                    }
                elif key == 'foods' or key == 'varietals':
                    result[key] = self._generate_list(value, depth)
                elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                    result[key] = self._generate_list(value, depth)
                elif isinstance(value, dict):
                    result[key] = self._generate_from_template(value, depth)
                elif value is False:
                    result[key] = self._generate_bool()
                elif value == 'string':
                    result[key] = self._generate_string(key)
                elif value == 'decimal':
                    result[key] = self._generate_decimal()
                elif value == 'integer':
                    result[key] = self._generate_integer()
                else:
                    result[key] = None
            return result

        return None

    def generate(self, template: Dict[str, Any], count: int) -> List[Dict[str, Any]]:
        result = []
        for _ in range(count):
            item = self._generate_from_template(template)
            # Убедимся, что description > 200 символов
            for lang_key in ['description', 'description_ru', 'description_fr']:
                if lang_key in item:
                    while len(item[lang_key]) < 200:
                        faker = self.fakers[lang_key.split('_')[1]]
                        item[lang_key] += " " + " ".join(faker.sentences(nb=3))
                    item[lang_key] = item[lang_key][:500]  # ограничим длину
            result.append(item)
        return result


def generate_test_data(
        model: Type[BaseModel], n: int, factory_kwargs: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Генерирует n тестовых данных для указанной Pydantic-модели с использованием Polyfactory.
    Совместимо с Pydantic 2+.

    Args:
        model: Pydantic-модель (возможно с вложенными моделями)
        n: количество генерируемых экземпляров
        factory_kwargs: дополнительные аргументы для кастомизации фабрики
            - faker_seed: int - seed для Faker (для воспроизводимых результатов)
            - set_as_default_factory: bool - установить фабрику как дефолтную для модели
            - providers: Dict[Type, Callable] - кастомные провайдеры для типов данных
            - field_overrides: Dict[str, Any] - переопределения для конкретных полей
            - int_range: Union[Dict[str, Tuple[int, int]], Tuple[int, int]] - диапазоны для целочисленных полей
            - float_range: Union[Dict[str, Tuple[float, float]], Tuple[float, float]] - диапазоны для полей с плавающей точкой
            - decimal_range: Union[Dict[str, Tuple[float, float]], Tuple[float, float]] - диапазоны для Decimal полей

    Returns:
        Список словарей с тестовых данных
    ПРИМЕР ИСПОЛЬЗОВАНИЯ
    test_data = generate_test_data(DrinkCreate, 8, {
    'int_range': (1, 5),
    'decimal_range': (0.5, 1),
    'float_range': {'price': (50.0, 200.0)},
    'field_overrides': {'name': 'Special Product'},
    'faker_seed': 42
    """
    if not model:
        print('generate_test_data.error: no model')
        return
    if not hasattr(model, 'model_fields'):
        print(f'model {model} has no attribute "model_fieldas"')

    factory_kwargs = factory_kwargs or {}

    # Извлекаем настройки диапазонов
    int_range = factory_kwargs.pop('int_range', {})
    float_range = factory_kwargs.pop('float_range', {})
    decimal_range = factory_kwargs.pop('decimal_range', {})

    # Обрабатываем глобальные диапазоны (если переданы как кортеж, а не словарь)
    global_int_range = int_range if isinstance(int_range, tuple) else None
    global_float_range = float_range if isinstance(float_range, tuple) else None
    global_decimal_range = decimal_range if isinstance(decimal_range, tuple) else None

    # Функция для определения базового типа поля (учитывая Optional и Union)
    def get_base_type(field_type):
        origin = get_origin(field_type)
        if origin is Union or origin is Optional:
            # Для Optional и Union извлекаем не-None типы
            args = [arg for arg in get_args(field_type) if arg is not type(None)]
            return args[0] if args else field_type
        return field_type

    # Если переданы глобальные диапазоны, преобразуем их в словари для отдельных полей
    if global_int_range:
        int_range = {}
        for field_name, field_info in model.model_fields.items():
            base_type = get_base_type(field_info.annotation)
            if hasattr(base_type, '__name__') and base_type.__name__ == 'int':
                int_range[field_name] = global_int_range

    if global_float_range:
        float_range = {}
        for field_name, field_info in model.model_fields.items():
            base_type = get_base_type(field_info.annotation)
            if hasattr(base_type, '__name__') and base_type.__name__ == 'float':
                float_range[field_name] = global_float_range

    if global_decimal_range:
        decimal_range = {}
        for field_name, field_info in model.model_fields.items():
            base_type = get_base_type(field_info.annotation)
            if hasattr(base_type, '__name__') and base_type.__name__ == 'Decimal':
                decimal_range[field_name] = global_decimal_range

    # Добавляем обработку Decimal по умолчанию
    default_providers = {Decimal: lambda: Decimal(round(random.uniform(1, 1000), 2))}

    # Объединяем с пользовательскими провайдерами
    custom_providers = factory_kwargs.pop('providers', {})
    providers = {**default_providers, **custom_providers}

    # Создаем кастомную фабрику
    class CustomFactory(ModelFactory):
        __model__ = model

        @classmethod
        def get_provider_map(cls):
            base_providers = super().get_provider_map()
            return {**base_providers, **providers}

    # Применяем field_overrides если они есть
    field_overrides = factory_kwargs.pop('field_overrides', {})
    for field_name, value in field_overrides.items():
        setattr(CustomFactory, field_name, value)

    # Добавляем обработку диапазонов для полей
    for field_name, (min_val, max_val) in int_range.items():
        setattr(
            CustomFactory, field_name, classmethod(
                lambda cls, mn=min_val, mx=max_val: random.randint(mn, mx)
            )
        )

    for field_name, (min_val, max_val) in float_range.items():
        setattr(
            CustomFactory, field_name, classmethod(
                lambda cls, mn=min_val, mx=max_val: random.uniform(mn, mx)
            )
        )

    for field_name, (min_val, max_val) in decimal_range.items():
        setattr(
            CustomFactory, field_name, classmethod(
                lambda cls, mn=min_val, mx=max_val: Decimal(round(random.uniform(mn, mx), 2))
            )
        )

    # Создаем динамическую фабрику для модели
    factory_class = type(
        f"{model.__name__}Factory", (CustomFactory,), {"__model__": model, **factory_kwargs}
    )

    # Генерируем данные
    result = (factory_class.build().model_dump() for _ in range(n))
    return (validate_and_fix_numeric_ranges(val, int_range=(1, n // 2), float_range=(0.1, 1.0)) for val in result)


def dict_validator(source: dict, n: int = 3) -> dict:
    if isinstance(source, dict):
        for key, val in source.items():
            # if key in ('sugar', 'alcc', 'aging', 'price', 'volume')
            #    print(f'========{key}: {val}== {type(val)}')
            if isinstance(val, Union[dict, list]):
                source[key] = dict_validator(val, n)
            elif isinstance(val, int):
                if key.endswith('_id'):
                    source[key] = 1  # randint(1, n)
                else:
                    source[key] = randint(1, 100)
            elif isinstance(val, float):
                source[key] = random.uniform(0.1, 25.0)
            elif isinstance(val, bool):
                source[key] = True
        return source
    elif isinstance(source, list):
        tmp: list = []
        for val in source:
            if isinstance(val, Union[dict, list]):
                tmp.append(dict_validator(val, n))
            elif isinstance(val, int):
                tmp.append = randint(1, 100)
            elif isinstance(val, float):
                tmp.append(random.uniform(0.1, 25.0))
            elif isinstance(val, bool):
                tmp.append(True)
            else:
                tmp.append(val)
        return tmp
