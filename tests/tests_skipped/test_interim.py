# tests/test_interim.py
"""
    тестирование всякоразного
"""
from pathlib import Path
# from fastapi import status
import datetime
import pytest
from app.core.config.project_config import get_path_to_root, settings
from app.core.utils.common_utils import jprint  # NOQA: F401
from pydantic import ValidationError
from app.core.utils.io_utils import get_filepath_from_dir_by_name
from app.support.item.schemas import ItemCreateRelation, DrinkCreateRelation  # noqa: F401

pytestmark = pytest.mark.asyncio

trob = ["-Lymvm4_ThSSpUZ-RzFJ.png",
        "-Lyn3fPXJtUnleVAwC_V.png",
        "-Lyn77KU1LO4tcXMcPSo.png",
        "-LynA8QtpDfTRKK57ByK.png",
        "-LynGOOQFp0REbzpfUDh.png",
        "-M-B8gu3HCcEg1GsGS4w.png",
        "-M-BCjRNX51_aXLnE5Tz.png",
        "-M-BPmDfQ_6SFQt6DYDV.png",
        "-M-H-6Vqv2xyFxi9thR6.png",
        "-M-HClMqkS6-dyc4-RPb.png",
        "-M-HHyXBoDGgP56aBact.png",
        "-M-K2SvlvwyyB2iPesIP.png",
        "-M-OWs4Zsnf8gwj-inrS.png",
        "-M-OY6Esn6kDmU8-iKD1.png",
        "-M-Vv-2y2zZpLrt8UFtm.png",
        "-M-ZkvcdAWggCg5RhD_r.png",
        "-M-Zkw1F4VLAELGpjVtp.png",
        "-M-djwPhHZL0MM9ckn6t.png",
        "-M-dpHCx7YXT02Rv4a6h.png",
        "-M-dwB-70_y2cwj3zVKM.png",
        "-M-dyzI_JfxJ746M4Pg0.png",
        "-M-ff1Prk4uJ9HN5wSHi.png",
        "-M-fi8G2Ji3N-A04WBNk.png",
        "-M-nzeMiaO-_fko65t4K.png",
        "-M-omf-mviBwV14qcBXG.png",
        "-M-u2E-1hWVfklAU7LdD.png",
        "-M0HzVjRTq879OetWmGG.png",
        "-M0Sq_blYYRNNUEzKZXy.png",
        "-M0SxgOBILvEUI7kgOIX.png",
        "-M0T-dopt_b_58tXij_y.png",
        "-M0anZ356ynkzYQB0dOA.png",
        "-M0d1sj6sSGfnNQjAqY4.png",
        "-M1-pwMtIYLNPk1jpa1S.png",
        "-M1WJHPtFAOMYRr5P2ky.png",
        "-MMntnF9o5tued3eFjKw.png",
        "-MpkT2abSS0ppLuShtwB.png",
        "-MsPkbFPgweM59aiSarL.png",
        "-MsQkrd84HBBZ94nTRbR.png",
        "-MwedlcQrcJtiq-rXD1_.png",
        "-OIVS-p8nqtKnO0GzX4c.png",
        "-OIVfSO8XXgmwDbIAeer.png",
        "-OIXNXypGv_FHQWcQ3vn.png",
        "-OIXY5GhDh3aHUZ_YwBQ.png",
        "-OIXeamXbuc8d8em2Ksk.png",
        "-OI_QLGPxQvHm3KPR68z.png",
        "-OI_V8M-DD97v5QCVMuq.png",
        "-OI_bSCFgtyPRN5xqIb5.png",
        "-OIbMxlmffSsaKwddCu8.png",
        "-OIbS7K9nu7iw-VcdHaO.png",
        "-OIbYNctD-egrepFz4ER.png",
        "-OIbfLSrTlhW28GIGDCJ.png",
        "-OIbpopAiQkIQZ4gOnc5.png"
        ]

model_list = ['Category',
              'Country',
              'Drink',
              'Food',
              'Item',
              'Region',
              'Subcategory',
              'Subregion',
              'Sweetness',
              'Varietal']
mandatory_sets = ['Read',
                  'Create',
                  'Update',
                  'CreateRelation',
                  'ReadRelation',
                  'CreateResponseSchema'
                  ]


def test_get_path_to_root():
    from app.core.utils.common_utils import enum_to_camel
    from app.core.utils.io_utils import read_file_lines_stripped
    """
        тестирование функции get_path_to_root
    """
    upload_dir = settings.UPLOAD_DIR
    file = 'country.json'
    dirname = get_path_to_root(f'{upload_dir}')
    assert dirname, f'file of directory "{upload_dir}" is not exist'
    assert isinstance(dirname, Path), 'method "get_path_to_root" return unexpected result'
    filepath = dirname / file
    result = read_file_lines_stripped(filepath)
    assert isinstance(result, list)
    expected_result = {a: enum_to_camel(a) for a in result}
    assert isinstance(expected_result, dict)


def test_enum_to_camel_and_back():
    """
        тестирует методы
        read_enum_to_camel
        enum_to_camel
        camel_to_enum
    """
    from app.core.utils.io_utils import read_enum_to_camel
    from app.core.utils.common_utils import enum_to_camel, camel_to_enum
    file = 'country.json'
    result = read_enum_to_camel(file)
    assert isinstance(result, dict)
    for key, val in result.items():
        assert enum_to_camel(key) == val, f'1: {key=} {val=} {enum_to_camel(key)=}'
        assert camel_to_enum(val) == key, f'2: {key=} {val=} {camel_to_enum(val)=}'


def test_get_filepath_from_dir():
    """
    тестирование метода get_filepath_from_dir
    проверяем как работает без аргументов
    """
    from app.core.utils.io_utils import get_filepath_from_dir
    result = get_filepath_from_dir()
    assert isinstance(result, list), f'получен неожидаемый ответ  {type(result)}'
    for key in result:
        assert isinstance(key, Path), f'ответ не сооветствует ожидаемому. {key}'


def test_get_filepath_from_dir_by_name():
    """
    тестирование метода get_filepath_from_dir_by_name (получение data.json)
    """
    result = get_filepath_from_dir_by_name()
    assert isinstance(result, Path), f'получен неожидаемый ответ  {type(result)}'


def test_compaire_image_json():
    """
    сравниваем список рисунков и json
    """
    from app.core.utils.io_utils import get_filepath_from_dir, readJson
    filepath = get_filepath_from_dir_by_name()
    images_file_name: list = [file.stem for file in get_filepath_from_dir()]
    json_images = list(readJson(filepath).get('items'))
    images_ommited = [img for img in images_file_name if img not in json_images]
    json_extra = [img for img in json_images if img not in images_file_name]
    print('json_extra')
    jprint(json_extra)
    print('images ommited')
    jprint(images_ommited)
    # assert False, f'{len(json_images)=}::{len(images_file_name)}'
    assert not images_ommited, images_ommited
    assert not json_extra, json_extra


def test_jsonconverter():
    """
    тестирует конвертацию 
    1. data.json -> JsonConverter
    2. -> dict
    3. -> ItemCreateRelation
    4. -> обратно в dict
    сравнивает результаты действий 2 и 4
    """
    from app.core.utils.alchemy_utils import JsonConverter
    filepath = get_filepath_from_dir_by_name()
    print('==================', filepath)
    JsonConv = JsonConverter(filepath)()
    for n, (key, item) in enumerate(JsonConv.items()):
        try:
            pymodel = ItemCreateRelation(**item)
            back_item = pymodel.model_dump(exclude_unset=True)
            assert item == back_item, (f"валидация исходных данных не прошла. см. diff в лога. "
                                       f"скорее всего проблема в именах ключей или формате значений (int vs str)"
                                       f" {key}")
        except ValidationError as e:
            print("Validation errors:")
            for error in e.errors():
                print(f"  Field: {' -> '.join(str(loc) for loc in error['loc'])}")
                print(f"  Type: {error['type']}")
                print(f"  Message: {error['msg']}")
                print(f"  Input: {error['input']}")
                print()
            assert False, "Validation failed"
    print(f'number of records is {n=}')


def test_jsonconverter2():
    """
    тестируем 'битые записи'
    тестирует исходные данные (если выбрасывает - см. diff)
    """
    from app.core.utils.alchemy_utils import JsonConverter
    from app.core.utils.common_utils import compare_dicts, compare_dict_keys
    filepath = get_filepath_from_dir_by_name()
    shit_list = [a.rstrip('.png') for a in trob]

    JsonConv = JsonConverter(filepath)()
    temp = next(iter(JsonConv.values()))
    for n, (key, item) in enumerate(JsonConv.items()):
        if key not in shit_list:
            continue
        print('-------------------')
        diff = compare_dict_keys(temp, item)
        print(diff)
        assert False
        assert not diff, key
        # assert temp == item, f'{type(temp)=}, {type(item)=}'


def test_source_constraint_data():
    """
        тестирование исходных данных на ограничение по уникальности
    """
    from app.core.utils.alchemy_utils import JsonConverter
    filepath = get_filepath_from_dir_by_name()
    JsonConv = JsonConverter(filepath)()
    drinks: dict = {}
    for n, (key, item) in enumerate(JsonConv.items()):
        try:
            if n == 1:
                jprint(item.get('drink'))
            drink = DrinkCreateRelation(**item.get('drink'))
        except ValidationError as e:
            print("Validation errors:")
            for error in e.errors():
                print(f"  Field: {' -> '.join(str(loc) for loc in error['loc'])}")
                print(f"  Type: {error['type']}")
                print(f"  Message: {error['msg']}")
                print(f"  Input: {error['input']}")
                print()
            assert False, "Validation failed"
        if drinks.get((drink.title, drink.subtitle)):
            expected_result = drinks.get((drink.title, drink.subtitle))
            assert expected_result.model_dump(exclude_unset=True) == drink.model_dump(exclude_unset=True), drink.title
        else:
            drinks[(drink.title, drink.subtitle)] = drink
    # assert False


async def test_items_direct_import_image(authenticated_client_with_db,
                                         test_db_session
                                         ):
    """
        Тестирует импорт изображений из директории
        и последующий импорт data.json c relation & image_id
        очень долгий тест
    """
    from app.mongodb.router import directprefix, prefix
    client = authenticated_client_with_db
    # загрузка файлов из upload_dir
    response = await client.post(f'{prefix}/{directprefix}')
    assert response.status_code == 200, response.text


async def test_items_direct_import_data(authenticated_client_with_db,
                                        test_db_session
                                        ):
    """
        тестирует метод items.direct_import_data
    """
    from app.mongodb.router import directprefix, prefix
    from app.support.item.router import ItemRouter as Router
    client = authenticated_client_with_db
    # загрузка файлов из upload_dir
    response = await client.post(f'{prefix}/{directprefix}')
    assert response.status_code == 200, response.text
    # загрузка из data.json
    router = Router()
    prefix = router.prefix
    response = await client.post(f'{prefix}/direct')
    assert response.status_code == 200, response.text
    result = response.json()
    error_nmbr = result.get('error_nmbr')
    assert error_nmbr == 0, result


def test_get_sqlalchemy_fields():
    """ тест процедуры получения полей sqlalchemy модели"""
    from sqlalchemy import ColumnElement
    from app.core.utils.alchemy_utils import get_sqlalchemy_fields
    from app.support.subregion.model import Subregion
    result = get_sqlalchemy_fields(Subregion, ['description*', '*ru', '*ion*'])
    assert isinstance(result, dict)
    for key, val in result.items():
        assert isinstance(val, ColumnElement), 'type is not ColumnElement'
        assert key == val.name


def test_pyschema_list():
    """ сверяет каких pydantic схем нехватает """
    from app.service_registry import get_all_pyschema
    mandatory_sets = ['Read',
                      'Create',
                      'Update',
                      'CreateRelation',
                      'ReadRelation',
                      'CreateResponseSchema'
                      ]
    mandatory_schema = [f'{model}{schema}' for model in model_list for schema in mandatory_sets]
    registered_schemas: dict = get_all_pyschema()
    for n, key in enumerate(registered_schemas.keys()):
        print(n, key)
    print('--------------------------')
    missed_schemas = [schema for schema in mandatory_schema if schema.lower() not in registered_schemas.keys()]
    if missed_schemas:
        for key in missed_schemas:
            print(f'{key}')
        assert False
    assert True


def test_repo_list():
    """ сверяет каких repositories нехватает """
    from app.service_registry import get_all_repo

    registered_repo: dict = get_all_repo()
    for n, key in enumerate(registered_repo.keys()):
        print(n, key)
    print('--------------------------')
    missed_repo = [model for model in model_list if model.lower() not in registered_repo.keys()]
    if missed_repo:
        for n, key in enumerate(missed_repo):
            print(f'{key}')
        assert False
    assert False


def test_services_list():
    """ сверяет каких services нехватает """
    from app.service_registry import get_all_services
    registered_services: dict = get_all_services()
    for n, key in enumerate(registered_services.keys()):
        print(n, key)
    print('--------------------------')
    missed_repo = [model for model in model_list if model.lower() not in registered_services.keys()]
    if missed_repo:
        for n, key in enumerate(missed_repo):
            print(f'{key}')
        assert False
    assert False


def test_get_pyschema():
    """
    проверяем как действует метод регистр репозиториев
    :return:
    :rtype:
    """
    from app.core.utils.pydantic_utils import get_pyschema
    from app.service_registry import get_all_pyschema
    from app.support.category.model import Category
    for key in mandatory_sets:
        schema = get_pyschema(Category, key)
        expected_result = f'{Category.__name__}{key}'
        assert schema, f'{Category.__name__}{key} схема не получена'
        assert schema.__name__ == expected_result, f'получено {schema.__name__}. Ожидалось {Category.__name__}{key}'
        for model in model_list:
            schema = get_pyschema(model, key)
            expected_result = f'{model}{key}'
            assert schema, f'{model}{key} схема не получена'
            assert schema.__name__ == expected_result, f'получено {schema.__name__}. Ожидалось {model}{key}'
        all = get_all_pyschema()
        for n, key in enumerate(all):
            print(n, key)
        assert False


def test_get_repo():
    """
    проверяем как действует метод get_repo
    :return:
    :rtype:
    """
    from app.core.utils.pydantic_utils import get_repo
    from app.support.category.model import Category
    item = get_repo(Category)
    expected_result = f'{Category.__name__}Repository'
    assert item, f'Repository для модели {Category.__name__} не получен'
    assert item.__name__ == expected_result, f'получено {item.__name__}. Ожидалось {Category.__name__}Repository'
    missed = [model for model in model_list if f'{model}Repository' != get_repo(model).__name__]
    if missed:
        for n, key in enumerate(missed):
            print(n, key)
        assert False, 'repo are missed for the model above'


def test_get_services():
    """
    проверяем как действует метод get_service
    :return:
    :rtype:
    """
    from app.core.utils.pydantic_utils import get_service
    from app.support.category.model import Category
    item = get_service(Category)
    expected_result = f'{Category.__name__}Service'
    assert item, f'Service для модели {Category.__name__} не получен'
    assert item.__name__ == expected_result, f'получено {item.__name__}. Ожидалось {Category.__name__}Service'
    missed = [model for model in model_list if f'{model}Service' != get_service(model).__name__]
    if missed:
        for n, key in enumerate(missed):
            print(n, key)
        assert False, 'services are missed for the model above'


def test_routers_list():
    from app.main import app
    from app.core.utils.pydantic_utils import get_routers
    result = get_routers(app)
    for route in result:
        print(route)
    assert False


def test_flatten_dict_with_localized_fields():
    from app.core.utils.common_utils import flatten_dict_with_localized_fields
    data = {"description": "english shg d",
            "description_ru": "русск",
            "description_fr": "francaise",
            "updated_at": "some data",
            "name": "Novokuznetsk",
            "name_ru": "Новокузнецк",
            "id": 100,
            "district": {
                "name": "Kemerovo region",
                "name_ru": "Кемеровская область",
                "id": 50,
                "country": {"name": "Russia",
                            "name_ru": "Россия",
                            "id": 7
                            }
            }
            }
    data = {'name': None, 'id': 3,
            'created_at': datetime.datetime(2025, 11, 5, 7, 22, 15, 170061,
                                            tzinfo=datetime.timezone.utc), 'name_ru': None,
            'description_ru': 'Нервно исследование хозяйка валюта. Еврейский райком товар пропаганда кольцо багровый.'
                              '\nСомнительный терапия развернуться издали посидеть пламя. '
                              'Строительство второй выкинуть возмутиться точно песня страсть. '
                              'Ребятишки князь предоставить виднеться. Пасть привлекать болото жестокий.',
            'category_id': 8,
            'description': 'Field wear time establish kid. Cup choose indeed ball fund decision. '
                           'Discuss argue growth common.\nThem include no because management government onto. '
                           'Today Congress responsibility.\nSport economic have some. Born present main suffer drug. '
                           'Floor work response check little place.',
            'updated_at': datetime.datetime(2025, 11, 5, 7, 22, 15, 170061, tzinfo=datetime.timezone.utc),
            'name_fr': 'Terrain prêt goutte claire.', 'description_fr': None, 'drinks': [],
            'category': {'id': 8, 'name': 'Image edge clear where.',
                         'created_at': datetime.datetime(2025, 11, 5, 7, 22, 15, 109514, tzinfo=datetime.timezone.utc),
                         'name_ru': 'Жидкий неожиданно решение.', 'description_ru': None, 'description': None,
                         'updated_at': datetime.datetime(2025, 11, 5, 7, 22, 15, 109514, tzinfo=datetime.timezone.utc),
                         'name_fr': 'Donner neuf cesser franc.', 'description_fr': None}}

    fields = ('name', 'description')
    print({key for key in data.keys() if any((key.startswith(fields), key == 'id'))})
    print(flatten_dict_with_localized_fields(data, ['name', 'description'], lang='ru', reverse=True))
    print(flatten_dict_with_localized_fields(data, ['name', 'description'], lang='en', reverse=False))
    assert False


def test_coalesce():
    from app.core.utils.common_utils import coalesce
    test = ["", '1', 2, None]
    result = coalesce(*test)
    exp = '1'
    assert result == exp, result


def test_jsonconverter3():
    """
    выдает на консоль рузельтат конвертации JsonConverter
    """
    from app.core.utils.alchemy_utils import JsonConverter
    filepath = get_filepath_from_dir_by_name('test.json')
    print(filepath)
    # конвертирует json в словарь relation
    JsonConv = JsonConverter(filepath)()
    jprint(JsonConv)
    assert False


def test_dict_compaire():
    from deepdiff import DeepDiff
    dict1 = {'drink': {'title': 'Bolgheri Sassicaia 2014 DOC', 'title_ru': 'Bolgheri Sassicaia 2014 DOC',
                       'subtitle': 'Tenuta San Guido', 'subtitle_ru': 'Tenuta San Guido',
                       'description': 'Intense, concentrated and deep ruby-colored, this wine offers elegant, complex aromas of red fruits. In the mouth it is rich and dense, but harmonious, with sweet, balanced tannins. \nThe wine has a long finish with a depth and structure that ensure its extraordinary longevity.',
                       'description_ru': 'Насыщенное, полнотелое вино, глубокого рубинового оттенка предлагает элегантные, сложные ароматы красных фруктов. Вино имеет богатый и плотный, но гармоничный вкус, со сладкими, сбалансированными танинами. \nОбладает послевкусием с глубиной и структурой, обеспечивающей его необычайную продолжительность.',
                       'subcategory': {'category': {'name': 'Wine'}, 'name': 'Red'},
                       'subregion': {'region': {'country': {'name': 'Italy'}, 'name': 'Tuscany', 'name_ru': 'Тоскана'},
                                     'name': 'Bolgheri', 'name_ru': 'Болгери'}, 'alc': 13.5, 'foods': [
                           {'superfood': {'name': 'Unclassified', 'name_ru': 'Не классифицированный'},
                            'name': 'Game (venison)', 'name_ru': 'Дичь'},
                           {'superfood': {'name': 'Unclassified', 'name_ru': 'Не классифицированный'}, 'name': 'Lamb',
                               'name_ru': 'Баранина'}], 'varietals': [
                           {'varietal': {'name': 'Cabernet Sauvignon', 'name_ru': 'Каберне Совиньон'}, 'percentage': 85.0},
                           {'varietal': {'name': 'Cabernet Franc', 'name_ru': 'Каберне Фран'}, 'percentage': 15.0}]},
             'vol': 0.75, 'count': 0, 'image_path': '-Lymluc5yKRoLQyYLbJG.png', 'image_id': '692642c8c072491af2d85ea9'}
    dict2 = {'image_id': '692642c8c072491af2d85ea9',
             'drink': {'title': 'Bolgheri Sassicaia 2014 DOC', 'title_ru': 'Bolgheri Sassicaia 2014 DOC',
                       'subtitle': 'Tenuta San Guido', 'subtitle_ru': 'Tenuta San Guido',
                       'description': 'Intense, concentrated and deep ruby-colored, this wine offers elegant, complex aromas of red fruits. In the mouth it is rich and dense, but harmonious, with sweet, balanced tannins. \nThe wine has a long finish with a depth and structure that ensure its extraordinary longevity.',
                       'description_ru': 'Насыщенное, полнотелое вино, глубокого рубинового оттенка предлагает элегантные, сложные ароматы красных фруктов. Вино имеет богатый и плотный, но гармоничный вкус, со сладкими, сбалансированными танинами. \nОбладает послевкусием с глубиной и структурой, обеспечивающей его необычайную продолжительность.',
                       'subcategory': {'category': {'name': 'Wine'}, 'name': 'Red'},
                       'subregion': {'region': {'country': {'name': 'Italy'}, 'name': 'Tuscany', 'name_ru': 'Тоскана'},
                                     'name': 'Bolgheri', 'name_ru': 'Болгери'}, 'alc': 13.5, 'id': 1}, 'vol': 0.75,
             'count': 0, 'image_path': '-Lymluc5yKRoLQyYLbJG.png'}

    diff = DeepDiff(dict1, dict2,
                    exclude_paths=["root['price']",
                                   "root['id']",
                                   "root['drink']['id']",
                                   "root['drink']['foods']",
                                   "root['drink']['varietals']"])
    assert not diff
