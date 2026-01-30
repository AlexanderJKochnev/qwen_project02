# tests/tests_utils/test_p2.py
""" тестирования метода подготовки индекса """
from app.core.utils.common_utils import jprint

import pytest
from rich.progress import track
from rich.console import Console
from rich.table import Table
from tests.data_factory.fake_generator import generate_test_data
from tests.conftest import get_model_by_name
pytestmark = pytest.mark.asyncio

items = {
    "image_id": "68e7f8002dc65c2a1d0a3241",
    "image_path": "-Lymluc5yKRoLQyYLbJG.png",
    "id": 1,
    "drink": {
        "title_ru": "Bolgheri Sassicaia 2014 DOC",
        "title_fr": "Bolgheri Sassicaia 2014 DOC",
        "subtitle": "Tenuta San Guido",
        "subtitle_ru": "Tenuta San Guido",
        "subtitle_fr": "Tenuta San Guido",
        "description": "Intense, concentrated and deep ruby-colored, this wine offers elegant, complex aromas of red fruits. In the mouth it is rich and dense, but harmonious, with sweet, balanced tannins. \nThe wine has a long finish with a depth and structure that ensure its extraordinary longevity.",
        "description_ru": "Насыщенное, полнотелое вино, глубокого рубинового оттенка предлагает элегантные, сложные ароматы красных фруктов. Вино имеет богатый и плотный, но гармоничный вкус, со сладкими, сбалансированными танинами. \nОбладает послевкусием с глубиной и структурой, обеспечивающей его необычайную продолжительность.",
        "description_fr": "Intense, concentré et de couleur rubis profond, ce vin offre des arômes élégants et complexes de fruits rouges. En bouche, il est riche et dense, mais harmonieux, avec des tanins doux et équilibrés. \nLe vin a une longue finale avec une profondeur et une structure qui assurent sa longévité extraordinaire.",
        "recommendation": "",
        "recommendation_ru": "",
        "recommendation_fr": "",
        "madeof": "",
        "madeof_ru": "",
        "madeof_fr": "",
        "title": "Bolgheri Sassicaia 2014 DOC",
        "subcategory": {
            "category": {
                "description": None,
                "description_ru": None,
                "description_fr": None,
                "description_es": None,
                "description_it": None,
                "description_de": None,
                "description_zh": None,
                "name": "Wine",
                "name_ru": "Вино",
                "name_fr": "Vin",
                "name_es": None,
                "name_it": None,
                "name_de": None,
                "name_zh": None,
                "id": 1
            },
            "description": "",
            "description_ru": "",
            "description_fr": "",
            "description_es": None,
            "description_it": None,
            "description_de": None,
            "description_zh": None,
            "name": "Red",
            "name_ru": "Красное",
            "name_fr": "Rouge",
            "name_es": None,
            "name_it": None,
            "name_de": None,
            "name_zh": None,
            "id": 1
        },
        "sweetness": None,
        "subregion": {
            "region": {
                "country": {
                    "description": "",
                    "description_ru": "",
                    "description_fr": "",
                    "description_es": None,
                    "description_it": None,
                    "description_de": None,
                    "description_zh": None,
                    "name": "Italy",
                    "name_ru": "Италия",
                    "name_fr": "",
                    "name_es": None,
                    "name_it": None,
                    "name_de": None,
                    "name_zh": None,
                    "id": 1
                },
                "description": None,
                "description_ru": None,
                "description_fr": None,
                "description_es": None,
                "description_it": None,
                "description_de": None,
                "description_zh": None,
                "name": "Tuscany",
                "name_ru": "Тоскана",
                "name_fr": None,
                "name_es": None,
                "name_it": None,
                "name_de": None,
                "name_zh": None,
                "id": 1
            },
            "description": None,
            "description_ru": None,
            "description_fr": None,
            "description_es": None,
            "description_it": None,
            "description_de": None,
            "description_zh": None,
            "name": "Bolgheri",
            "name_ru": "Болгери",
            "name_fr": None,
            "name_es": None,
            "name_it": None,
            "name_de": None,
            "name_zh": None,
            "id": 1
        },
        "alc": "14%",
        "sugar": None,
        "age": "",
        "foods": [
            {
                "superfood": {
                    "description": "",
                    "description_ru": "",
                    "description_fr": "",
                    "description_es": None,
                    "description_it": None,
                    "description_de": None,
                    "description_zh": None,
                    "name": "Unclassified",
                    "name_ru": "Не классифицированный",
                    "name_fr": "Non classé",
                    "name_es": None,
                    "name_it": None,
                    "name_de": None,
                    "name_zh": None,
                    "id": 1
                },
                "description": None,
                "description_ru": None,
                "description_fr": None,
                "description_es": None,
                "description_it": None,
                "description_de": None,
                "description_zh": None,
                "name": "Game (venison)",
                "name_ru": "Дичь",
                "name_fr": None,
                "name_es": None,
                "name_it": None,
                "name_de": None,
                "name_zh": None,
                "id": 1
            },
            {
                "superfood": {
                    "description": "",
                    "description_ru": "",
                    "description_fr": "",
                    "description_es": None,
                    "description_it": None,
                    "description_de": None,
                    "description_zh": None,
                    "name": "Unclassified",
                    "name_ru": "Не классифицированный",
                    "name_fr": "Non classé",
                    "name_es": None,
                    "name_it": None,
                    "name_de": None,
                    "name_zh": None,
                    "id": 1
                },
                "description": None,
                "description_ru": None,
                "description_fr": None,
                "description_es": None,
                "description_it": None,
                "description_de": None,
                "description_zh": None,
                "name": "Lamb",
                "name_ru": "Баранина",
                "name_fr": None,
                "name_es": None,
                "name_it": None,
                "name_de": None,
                "name_zh": None,
                "id": 2
            }
        ],
        "varietals": [
            {
                "description": None,
                "description_ru": None,
                "description_fr": None,
                "description_es": None,
                "description_it": None,
                "description_de": None,
                "description_zh": None,
                "name": "Cabernet Franc",
                "name_ru": "Каберне Фран",
                "name_fr": None,
                "name_es": None,
                "name_it": None,
                "name_de": None,
                "name_zh": None,
                "id": 2
            },
            {
                "description": None,
                "description_ru": None,
                "description_fr": None,
                "description_es": None,
                "description_it": None,
                "description_de": None,
                "description_zh": None,
                "name": "Cabernet Sauvignon",
                "name_ru": "Каберне Совиньон",
                "name_fr": None,
                "name_es": None,
                "name_it": None,
                "name_de": None,
                "name_zh": None,
                "id": 1
            }
        ],
        "varietal_associations": [
            {
                "varietal": {
                    "description": None,
                    "description_ru": None,
                    "description_fr": None,
                    "description_es": None,
                    "description_it": None,
                    "description_de": None,
                    "description_zh": None,
                    "name": "Cabernet Franc",
                    "name_ru": "Каберне Фран",
                    "name_fr": None,
                    "name_es": None,
                    "name_it": None,
                    "name_de": None,
                    "name_zh": None
                },
                "percentage": 15
            },
            {
                "varietal": {
                    "description": None,
                    "description_ru": None,
                    "description_fr": None,
                    "description_es": None,
                    "description_it": None,
                    "description_de": None,
                    "description_zh": None,
                    "name": "Cabernet Sauvignon",
                    "name_ru": "Каберне Совиньон",
                    "name_fr": None,
                    "name_es": None,
                    "name_it": None,
                    "name_de": None,
                    "name_zh": None
                },
                "percentage": 85
            }
        ],
        "food_associations": [
            {
                "food": {
                    "superfood": {
                        "description": "",
                        "description_ru": "",
                        "description_fr": "",
                        "description_es": None,
                        "description_it": None,
                        "description_de": None,
                        "description_zh": None,
                        "name": "Unclassified",
                        "name_ru": "Не классифицированный",
                        "name_fr": "Non classé",
                        "name_es": None,
                        "name_it": None,
                        "name_de": None,
                        "name_zh": None,
                        "id": 1
                    },
                    "description": None,
                    "description_ru": None,
                    "description_fr": None,
                    "description_es": None,
                    "description_it": None,
                    "description_de": None,
                    "description_zh": None,
                    "name": "Game (venison)",
                    "name_ru": "Дичь",
                    "name_fr": None,
                    "name_es": None,
                    "name_it": None,
                    "name_de": None,
                    "name_zh": None,
                    "id": 1
                }
            },
            {
                "food": {
                    "superfood": {
                        "description": "",
                        "description_ru": "",
                        "description_fr": "",
                        "description_es": None,
                        "description_it": None,
                        "description_de": None,
                        "description_zh": None,
                        "name": "Unclassified",
                        "name_ru": "Не классифицированный",
                        "name_fr": "Non classé",
                        "name_es": None,
                        "name_it": None,
                        "name_de": None,
                        "name_zh": None,
                        "id": 1
                    },
                    "description": None,
                    "description_ru": None,
                    "description_fr": None,
                    "description_es": None,
                    "description_it": None,
                    "description_de": None,
                    "description_zh": None,
                    "name": "Lamb",
                    "name_ru": "Баранина",
                    "name_fr": None,
                    "name_es": None,
                    "name_it": None,
                    "name_de": None,
                    "name_zh": None,
                    "id": 2
                }
            }
        ],
        "updated_at": "2025-12-22T10:15:54.200422Z",
        "description_es": None,
        "description_it": None,
        "description_de": None,
        "description_zh": None,
        "id": 1
    },
    "vol": 0.75,
    "price": None,
    "count": 0
}


def test_prepare_search_string():
    from app.core.utils.pydantic_utils import prepare_search_string
    # 1. валидируем исходные данные
    try:
        # item = ItemReadRelation.validate(items)
        result = prepare_search_string(items)
        print('')
        print(result)
    except Exception as e:
        assert False, e


def test_registers_search_update(authenticated_client_with_db):
    """ проверка как регистрируются пути для обновленияя индекса vs зависимых моделей"""
    # from app.support.varietal.model import Varietal
    # from app.support.food.model import Food
    # from app.support.country.model import Country
    from app.core.utils.common_utils import get_owners_by_path
    from app.service_registry import _SEARCH_DEPENDENCIES

    console = Console()

    table = Table(title="Отчет по тестированию get_owners_by_path")

    table.add_column("MODEL", style="cyan", no_wrap=True)
    table.add_column("PATH", justify="right", style="magenta")
    table.add_column("owners", justify="right", style="green")
    # table.add_column('error', justify = "right", style = "red")
    for key, val in _SEARCH_DEPENDENCIES.items():
        owners = get_owners_by_path(key, val)
        if owners:
            owner_ids = [o.id for o in owners if hasattr(o, 'id')]
            print(key.__name__, owners, owner_ids)
        else:
            print(
                key.__name__, owners)
        table.add_row(key.__name__, val)
    console.print(table)
