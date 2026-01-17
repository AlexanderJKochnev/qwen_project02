# tests/tests_utils/test_item_service.py

import pytest
from rich.pretty import pprint
# from rich.progress import track
# from rich.console import Console
# from rich.table import Table
# from tests.data_factory.fake_generator import generate_test_data
# from tests.conftest import get_model_by_name
from app.core.config.project_config import settings

pytestmark = pytest.mark.asyncio

input_data: dict = {
    "id": 12,
    "image_id": "68e5f23f7b1dc3f495d4f82d",
    "image_path": "-Lymluc5yKRoLQyYLbJG.png",
    "drink": {
        "title_ru": "Bolgheri Sassicaia 2014 DOC",
        "title_fr": None,
        "subtitle": "Tenuta San Guido",
        "subtitle_ru": "Tenuta San Guido",
        "subtitle_fr": None,
        "description": "Intense, concentrated and deep ruby-colored, "
                       "this wine offers elegant, complex aromas of red fruits. "
                       "In the mouth it is rich and dense, but harmonious, with sweet, balanced tannins.",
        "description_ru": "Насыщенное, полнотелое вино, глубокого рубинового оттенка предлагает элегантные, "
                          "сложные ароматы красных фруктов.",
        "description_fr": None,
        "recommendation": None,
        "recommendation_ru": None,
        "recommendation_fr": None,
        "madeof": None,
        "madeof_ru": None,
        "madeof_fr": None,
        "title": "Bolgheri Sassicaia 2014 DOC",
        "subcategory": {
            "category": {
                "description": None,
                "description_ru": "Описание вина",
                "description_fr": None,
                "name": "Wine",
                "name_ru": "Вино",
                "name_fr": "Vin",
                "id": 1
            },
            "description": "very very very red",
            "description_ru": "самое красное вино из всех",
            "description_fr": None,
            "name": "Red",
            "name_ru": "Красное",
            "name_fr": "Rouge",
            "id": 1
        },
        "sweetness": {
            "description": None,
            "description_ru": None,
            "description_fr": None,
            "name": "Brut",
            "name_ru": "Брют",
            "name_fr": None,
            "id": 1
        },
        "subregion": {
            "region": {
                "country": {
                    "description": None,
                    "description_ru": None,
                    "description_fr": None,
                    "name": "Italy",
                    "name_ru": "Италия",
                    "name_fr": "Italie",
                    "id": 1
                },
                "description": "",
                "description_ru": None,
                "description_fr": None,
                "name": "Tuscany",
                "name_ru": "Тоскана",
                "name_fr": None,
                "id": 1
            },
            "description": None,
            "description_ru": None,
            "description_fr": None,
            "name": "Bolgheri",
            "name_ru": "Болгери",
            "name_fr": None,
            "id": 1
        },
        "alc": "14%",
        "sugar": None,
        "age": "",
        "foods": [
            {
                "superfood": {
                    "description": "",
                    "description_ru": "Мясо и мясные продукты",
                    "description_fr": "",
                    "name": "Meat",
                    "name_ru": "Мясо",
                    "name_fr": "Viande",
                    "id": 1
                },
                "description": None,
                "description_ru": None,
                "description_fr": None,
                "name": "Game (venison)",
                "name_ru": "С дичью",
                "name_fr": None,
                "id": 1
            },
            {
                "superfood": None,
                "description": "",
                "description_ru": "",
                "description_fr": "",
                "name": "Lamb",
                "name_ru": "Бараниной",
                "name_fr": "",
                "id": 2
            }
        ],
        "varietals": [
            {
                "description": None,
                "description_ru": None,
                "description_fr": None,
                "name": "Cabernet Sauvignon",
                "name_ru": "Каберне Совиньон",
                "name_fr": None,
                "id": 1
            },
            {
                "description": None,
                "description_ru": None,
                "description_fr": None,
                "name": "Cabernet Franc",
                "name_ru": "Каберне Фран",
                "name_fr": None,
                "id": 2
            }
        ],
        "varietal_associations": [
            {
                "varietal": {
                    "description": None,
                    "description_ru": None,
                    "description_fr": None,
                    "name": "Cabernet Sauvignon",
                    "name_ru": "Каберне Совиньон",
                    "name_fr": None
                },
                "percentage": 85
            },
            {
                "varietal": {
                    "description": None,
                    "description_ru": None,
                    "description_fr": None,
                    "name": "Cabernet Franc",
                    "name_ru": "Каберне Фран",
                    "name_fr": None
                },
                "percentage": 15
            }
        ],
        "food_associations": [
            {
                "food": {
                    "superfood": {
                        "description": "",
                        "description_ru": "Мясо и мясные продукты",
                        "description_fr": "",
                        "name": "Meat",
                        "name_ru": "Мясо",
                        "name_fr": "Viande",
                        "id": 1
                    },
                    "description": None,
                    "description_ru": None,
                    "description_fr": None,
                    "name": "Game (venison)",
                    "name_ru": "С дичью",
                    "name_fr": None,
                    "id": 1
                }
            },
            {
                "food": {
                    "superfood": None,
                    "description": "",
                    "description_ru": "",
                    "description_fr": "",
                    "name": "Lamb",
                    "name_ru": "Бараниной",
                    "name_fr": "",
                    "id": 2
                }
            }
        ],
        "updated_at": "2025-10-16T11:28:37.562289Z",
        "id": 1
    },
    "vol": 0.75,
    "price": None,
    "count": 0
}


output_data: dict = {
    "image_id": "68e5f23f7b1dc3f495d4f82d",
    "image_path": "-Lymluc5yKRoLQyYLbJG.png",
    "id": 1,
    "vol": 0.75,
    "changed_at": "2025-10-16T11:28:37.562289Z",
    "country": "italy",
    "category": "red",
    "en": {"description": "Intense, concentrated and deep ruby-colored, "
                          "this wine offers elegant, complex aromas of red fruits. "
                          "In the mouth it is rich and dense, but harmonious, with sweet, balanced tannins.",
           "subtitle": "Tenuta San Guido",
           "title": "Bolgheri Sassicaia 2014 DOC",
           "alc": "13.5%",
           "pairing": [
                "Game (venison)",
                "Lamb"
           ],
           "varietal": ["Cabernet Sauvignon 85%",
                        "Cabernet Franc 15%"]
           },
    "ru": {
        "description": "Насыщенное, полнотелое вино, глубокого рубинового оттенка предлагает элегантные, "
                       "сложные ароматы красных фруктов.",
        "subtitle": "Tenuta San Guido",
        "title": "Bolgheri Sassicaia 2014 DOC",
        "alc": "13.5%",
        "pairing": [
            "С дичью",
            "Бараниной"
        ],
        "varietal": [
            "Каберне Совиньон 85%",
            "Каберне Фран 15%"
        ]
    },
    "fr": {
        "description": "Intense, concentrated and deep ruby-colored, this wine offers elegant, "
                       "complex aromas of red fruits.",
        "subtitle": "Tenuta San Guido",
        "title": "Bolgheri Sassicaia 2014 DOC",
        "alc": "13.5%",
        "pairing": [
            "Game (venison)",
            "Lamb"
        ],
        "varietal": [
            "Cabernet Sauvignon 85%",
            "Cabernet Franc 15%"
        ]
    }
}


def test_get_api_view():
    """
         get_api_view
    """
    from app.support.item.service import ItemService as service, lang_suffix_list
    language = settings.LANGUAGES
    lang_prefixes: list = lang_suffix_list(language)
    # print(language)
    # print(lang_prefixes)
    # pprint(lang_dict, indent_guides=True, expand_all=True)
    # pprint(input_data, indent_guides=True, expand_all=False)
    result = service.__api_view__(input_data)
    pprint(result, indent_guides=True, expand_all=True)
