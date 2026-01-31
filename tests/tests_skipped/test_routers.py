# flake8: noqa: E501
# tests/test_routers.py
""" в этой директории тесты для тестирования
    - генератора тестовых данных
    - роутеров
    - схем
    рекомендуется запускать если будут падать тесты test_create, test_patch, test_get_one, test_delete
    pytest tests/test_routers.py --tb=auto --disable-warnings -vv --capture=no
"""

import pytest
from pydantic import TypeAdapter, ValidationError
import json
from app.core.utils.common_utils import jprint
from app.core.models.base_model import get_model_by_name


pytestmark = pytest.mark.asyncio


@pytest.mark.skip
async def test_get(authenticated_client_with_db, test_db_session, fakedata_generator):
    # from app.support.drink.router import DrinkRouter as Router
    from app.support.warehouse.router import WarehouseRouter as Router
    router = Router()
    prefix = router.prefix
    # create_schema = router.create_schema
    # patch_schema = router.patch_schema
    id = 2
    client = authenticated_client_with_db
    response = await client.get(f'{prefix}/{id}')
    assert response.status_code == 200
    result = response.json()
    print(f'<<<<<{result.keys()}>>>>')
    for key, val in result.items():
        print(f'{key}: {val}')
    assert True


@pytest.mark.skip
async def test_fakedata_generator(authenticated_client_with_db, test_db_session, get_fields_type):
    client = authenticated_client_with_db
    counts = 10
    for key, val in get_fields_type.items():
        try:
            for n in range(counts):
                route = key
                if n % 2 == 1:
                    data = {k2: v2() for k2, v2 in val['required_only'].items()}
                else:
                    data = {k2: v2() for k2, v2 in val['all_fields'].items()}
                response = await client.post(f'{route}', json=data)
                assert response.status_code == 200, f'{key}::{data}'
        except Exception as he:
            # if he.status_code != 409:
            #     # logger.warning(f"HTTP error in get_one: {he.detail}")
            assert False, f'error {he=}, {response.status_code=} {key}::{data}'


@pytest.mark.skip
async def test_patch(authenticated_client_with_db, test_db_session, fakedata_generator):
    from app.support.category.router import CategoryRouter as Router
    router = Router()
    prefix = router.prefix
    # create_schema = router.create_schema
    patch_schema = router.patch_schema
    data = {'description': 'changed_Now hour institution situation. '
                           'Training heart stand adult large health risk. '
                           'Do thought personal before try letter.',
            'description_ru': 'changed_Range important several short box picture. '
                              'Executive up hold push everything hotel. Professor source threat power. '
                              'Cover my middle.',
            'name_ru': 'changed_Christopher King',
            'name': 'changed_Anna Barton'}
    try:
        _ = patch_schema(**data)  # валидация входных данных
    except Exception as e:
        assert False, f'data validation error. {e}'
    id = 1
    client = authenticated_client_with_db
    response = await client.patch(f'{prefix}/{id}', json=data)
    assert response.status_code == 200
    result = response.json()
    for key, val in data.items():
        assert result.get(key) == val


@pytest.mark.skip
async def test_greenlet(authenticated_client_with_db, test_db_session):
    """ тестирование one_to_many relationships"""
    from app.support.customer.router import CustomerRouter as RouterMain
    from app.support.warehouse.router import WarehouseRouter as RouterSlave
    client = authenticated_client_with_db
    master: dict = {'login': 'name',
                    'firstname': 'name_ru',
                    'lastname': 'last_name'}
    slave: dict = {'customer_id': 1,
                   'name': 'name'}
    router_main = RouterMain()
    router_slave = RouterSlave()
    prefix_main = router_main.prefix
    prefix_slave = router_slave.prefix
    create_master = router_main.create_schema
    create_slave = router_slave.create_schema
    count = 3
    # валидация данных :
    try:
        _ = create_master(**master)
    except Exception as e:
        assert False, f'валидация мастер не прошла {e}'
    try:
        _ = create_slave(**slave)
    except Exception as e:
        assert False, f'валидация slave не прошла {e}'
    # генератор данных master
    data_master = [{key: f'{val}_{n}' for key, val in master.items()} for n in range(count)]
    for data in data_master:
        response = await client.post(f'{prefix_main}', json=data)
        assert response.status_code == 200, f'create for data_master error {data}'
    response = await client.get(f'{prefix_main}')
    assert response.status_code == 200, 'get for data_master error'
    result = response.json()

    # генератор данных slave
    for x in result['items']:
        try:
            data = {key: f"{val}_{x['id']}" for key, val in slave.items()}
            data['customer_id'] = 1
            response = await client.post(f'{prefix_slave}', json=data)
            assert response.status_code == 200, f"create for data_slave error {data}"
        except Exception as e:
            assert False, f"{e} {data=} {x['id']=}"


@pytest.mark.skip
async def test_search(authenticated_client_with_db, test_db_session, create_drink):
    """ тестирование поиска в drink """
    from random import randint
    client = authenticated_client_with_db
    prefix = '/drinks'
    id = create_drink
    response = await client.get(f'{prefix}/{id}')
    assert response.status_code == 200, response.text
    tmp = response.json()
    data = ' '.join((val.replace('.', ' ').replace('  ', '^ ').replace('^', '')
                     for val in tmp.values() if isinstance(val, str))).split(' ')
    query = data[randint(0, len(data) - 1)]
    assert query in data, f'{query} not in record investgated'
    params = {'query': query}
    response = await client.get(f'{prefix}/search', params=params)
    assert response.status_code == 200, response.text
    result = response.json().get('items')
    resp = [item for item in result if item.get('id') == id]
    assert resp, 'поиск выполнен неверно'


async def test_get_or_create(authenticated_client_with_db, test_db_session):
    from app.support.category.router import CategoryRouter
    client = authenticated_client_with_db
    router = CategoryRouter()
    create_schema = router.create_schema
    prefix = router.prefix
    data = {"name": "Design",
            "name_ru": "Заработать",
            "name_fr": "Mari",
            "description": "Cup operation discussion significant early budget parent skill. Fund admit challenge individual government. Anything school Democrat first success yet. Many well product. Another information process those again sure six care. Whose business task offer response bring enough. Begin student rock smile five note eight. Look front teach notice final.",
            "description_ru": "Зачем висеть смеяться кидать пропаганда художественный основание тусклый. Жить спалить лиловый возбуждение. Наткнуться редактор растеряться тяжелый ложиться материя. Построить наступать успокоиться. Скользить кузнец засунуть светило нервно заявление передо металл.",
            "description_fr": "Rouge mort habiter jeunesse rose. Inviter habitant feuille paix. Prière douceur angoisse moindre surveiller corps effacer sable. Sourd résoudre fou combien toit. Employer inquiétude salle tout ferme réfléchir."
            }
    try:
        _ = create_schema(**data)
    except Exception as e:
        assert False, f'Ошибка валидации данных: {e}'
    response = await client.post(f'{prefix}', json=data)
    assert response.status_code == 200, response.text
    response = await client.post(f'{prefix}', json=data)
    assert response.status_code == 200, response.text


@pytest.mark.skip
async def test_get_relation(authenticated_client_with_db, test_db_session):
    from app.support.subregion.router import SubregionRouter as Router
    # from app.support.region.router import RegionRouter as Router
    # from app.support.country.router import CountryRouter as Router
    from app.core.utils.common_utils import get_all_dict_paths, get_nested, set_nested, pop_nested
    client = authenticated_client_with_db

    router = Router()
    create_schema = router.create_schema
    create_schema_relation = router.create_schema_relation
    adapter = TypeAdapter(create_schema_relation)
    prefix = router.prefix
    service = router.service

    data = {
        "region": {
            "country": {
                "name": "Spain",
                "name_ru": "Испания",
                "name_fr": "Espagne",
                "description": "Spain is a country in Europe known for wine.",
                "description_ru": "Испания — страна в Европе, известная своими винами.",
                "description_fr": "Espagne est un pays d'Europe réputé pour son vin."
            },
            "name": "Rioja",
            "name_ru": "Рибера-дель-Дуэро",
            "name_fr": "Rioja",
            "description": "Rioja is a wine region in Spain.",
            "description_ru": "Рибера-дель-Дуэро — винный регион в Испания.",
            "description_fr": "Rioja est une région viticole en Espagne."
        },
        "name": "Alavesa",
        "name_ru": "Алавеса",
        "name_fr": "Alavesa",
        "description": "Alavesa is a subregion of Rioja.",
        "description_ru": "Алавеса — субрегион Рибера-дель-Дуэро.",
        "description_fr": "Alavesa est un sous-région de Rioja."
    }
    # data = data.get('region')
    # data = data.get('country')
    try:
        json_data = json.dumps(data)
        adapter.validate_json(json_data)
        assert True
    except ValidationError as e:
        assert False, f"Ошибка валидации входных данных. Errors: {e.errors()}"
    main_dict = {key: get_model_by_name(val) for key, val in get_all_dict_paths(data).items()}
    for key, val in main_dict.items():
        subdata = pop_nested(data, key)
        try:
            _ = val(**subdata)
        except Exception as e:
            assert False, f'{e}, {key}, {json.dumps(subdata, indent=2, ensure_ascii=False)}'
        set_nested(data, f'{key}_id', 1)
    try:
        _ = create_schema(**data)
    except Exception as e:
        assert False, f'валидация поcле обновления {e}'
    response = await client.post(f'{prefix}/relation', json=data)
    assert response.status_code == 200, response.text


async def test_new_data_generator(authenticated_client_with_db, test_db_session,
                                  simple_router_list, complex_router_list):
    from tests.data_factory.fake_generator import generate_test_data
    source = simple_router_list + complex_router_list
    test_number = 10
    client = authenticated_client_with_db
    for n, item in enumerate(source):
        router = item()
        schema = router.create_schema_relation
        adapter = TypeAdapter(schema)
        prefix = router.prefix
        test_data = generate_test_data(
            schema, test_number,
            {'int_range': (1, test_number),
             'decimal_range': (0.5, 1),
             'float_range': (0.1, 1.0),
             # 'field_overrides': {'name': 'Special Product'},
             'faker_seed': 42}
        )
        for m, data in enumerate(test_data):
            try:
                # _ = schema(**data)      # валидация данных
                json_data = json.dumps(data)
                adapter.validate_json(json_data)
                assert True
            except Exception as e:
                assert False, f'Error IN INPUT VALIDATION {e}, router {prefix}, example {m}'
            return
            try:
                response = await client.post(f'{prefix}', json=data)
                assert response.status_code == 200, f'||{prefix}, {response.text}'
            except Exception as e:
                assert False, f'{response.status_code=} {prefix=}, error: {e}, example {m}, {response.text}'


async def test_create_relations(authenticated_client_with_db, test_db_session,
                                simple_router_list, complex_router_list):
    from tests.data_factory.fake_generator import generate_test_data
    from app.support.subregion.router import (SubregionRouter, Subregion, SubregionRepository,
                                              SubregionCreate, SubregionService)
    from app.support.region.router import RegionRouter, Region, RegionRepository, RegionService, RegionCreate
    from app.support.country.router import CountryRouter, Country, CountryRepository, CountryService, CountryCreate
    from app.core.utils.common_utils import get_nested, set_nested
    from app.core.utils.common_utils import get_all_dict_paths
    # source = simple_router_list + complex_router_list
    stock = {'country': {'schema': CountryCreate,
                         'model': Country,
                         'repo': CountryRepository,
                         'service': CountryService},
             'region': {'schema': RegionCreate,
                        'model': Region,
                        'repo': RegionRepository,
                        'service': RegionService}
             }

    source = [SubregionRouter, ]
    test_number = 1
    client = authenticated_client_with_db
    for n, item in enumerate(source):
        router = item()
        schema = router.create_schema_relation
        create_schema = router.create_schema
        adapter = TypeAdapter(schema)
        prefix = router.prefix
        test_data = generate_test_data(
            schema, test_number,
            {'int_range': (1, test_number),
             'decimal_range': (0.5, 1),
             'float_range': (0.1, 1.0),
             # 'field_overrides': {'name': 'Special Product'},
             'faker_seed': 42}
        )
        for m, data in enumerate(test_data):
            try:
                # _ = schema(**data)      # валидация данных
                json_data = json.dumps(data)
                adapter.validate_json(json_data)
                assert True
            except Exception as e:
                assert False, f'Error IN INPUT VALIDATION {e}, router {prefix}, example {m}'
        vv = get_all_dict_paths(data)

        for key in get_all_dict_paths(data):
            idx = key.split('.')[-1]
            val: dict = stock[idx]
            ndata = get_nested(data, key)
            model_data = val['schema'](**ndata)
            result = await val['service'].get_or_create(model_data, val['repo'], val['model'], test_db_session)
            id = result.to_dict()['id']
            assert id, result
            if not idx.endswith('_id'):
                idx = f'{idx}_id'
            if '.' in key:  # уровень вложенности больше 1
                path = '.'.join((key.rsplit('.', 1)[0], idx))
                set_nested(data, path, id)
            else:
                data[idx] = id
                # assert False, f'{idx=}'
        model_data = create_schema(**data)
        result = await SubregionService.get_or_create(model_data, SubregionRepository, Subregion, test_db_session)
        return
        """country_data = get_nested(data, 'region.country')
        # response = await client.post(f'{prefix}', json = data)
        model_data = CountryCreate(**country_data)
        result = await CountryService.create(model_data, CountryRepository, Country, test_db_session)
        # test_db_session.commit()
        assert result.to_dict().get('id'), result
        region_data = get_nested(data, 'region')
        region_data['country_id'] = result.to_dict().get('id')
        model_data = RegionCreate(**region_data)
        result = await RegionService.create(model_data, RegionRepository, Region, test_db_session)
        assert result.to_dict().get('id'), result
        data['region_id'] = result.to_dict().get('id')
        model_data = SubregionCreate(**data)
        result = await SubregionService.create(model_data, SubregionRepository, Subregion, test_db_session)
        assert result.to_dict().get('id'), result
        test_db_session.commit()"""


async def test_create_region_relation(authenticated_client_with_db, test_db_session,
                                      simple_router_list, complex_router_list):
    from tests.data_factory.fake_generator import generate_test_data
    from app.support.region.router import RegionRouter, Region, RegionCreate, RegionCreateRelation
    # source = simple_router_list + complex_router_list
    test_number = 3
    client = authenticated_client_with_db
    router = RegionRouter()
    schema = router.create_schema_relation
    adapter = TypeAdapter(schema)
    prefix = router.prefix
    test_data = generate_test_data(schema, test_number,
                                   {'int_range': (1, test_number),
                                    'decimal_range': (0.5, 1),
                                    'float_range': (0.1, 1.0),
                                    # 'field_overrides': {'name': 'Special Product'},
                                    'faker_seed': 42})
    for data in test_data:
        try:
            json_data = json.dumps(data)
            adapter.validate_json(json_data)
        except Exception as e:
            assert False, e

        response = await client.post(f'{prefix}/hierarchy', json=data)
        assert response.status_code in [200, 201], f'{response.text}'


async def test_create_subregion_relation(authenticated_client_with_db, test_db_session,
                                         simple_router_list, complex_router_list):
    from tests.data_factory.fake_generator import generate_test_data
    from app.support.subregion.router import SubregionRouter  # , Region, RegionCreate, RegionCreateRelation
    # source = simple_router_list + complex_router_list
    test_number = 3
    client = authenticated_client_with_db
    router = SubregionRouter()
    schema = router.create_schema_relation
    adapter = TypeAdapter(schema)
    prefix = router.prefix
    test_data = generate_test_data(schema, test_number,
                                   {'int_range': (1, test_number),
                                    'decimal_range': (0.5, 1),
                                    'float_range': (0.1, 1.0),
                                    # 'field_overrides': {'name': 'Special Product'},
                                    'faker_seed': 42})
    for data in test_data:
        try:
            json_data = json.dumps(data)
            adapter.validate_json(json_data)
        except Exception as e:
            assert False, e

        response = await client.post(f'{prefix}/hierarchy', json=data)
        assert response.status_code in [200, 201], f'{response.text}'


async def test_create_drink_relation(authenticated_client_with_db, test_db_session,
                                     simple_router_list, complex_router_list):
    from tests.data_factory.fake_generator import generate_test_data
    from app.support.drink.router import DrinkRouter  # , Region, RegionCreate, RegionCreateRelation
    # source = simple_router_list + complex_router_list
    test_number = 20  # большое кол-во тестов может привести к ошибке - генератор float увеличивает
    # значения за пределы допустимого
    client = authenticated_client_with_db
    router = DrinkRouter()
    schema = router.create_schema_relation
    adapter = TypeAdapter(schema)
    prefix = router.prefix
    test_data = generate_test_data(schema, test_number,
                                   {'int_range': (1, test_number),
                                    'decimal_range': (0.5, 1),
                                    'float_range': (0.1, 1.0),
                                    # 'field_overrides': {'name': 'Special Product'},
                                    'faker_seed': 42})
    for data in test_data:
        try:
            json_data = json.dumps(data)
            adapter.validate_json(json_data)
        except Exception as e:
            print('================================')
            print(json.dumps(data, indent=2, ensure_ascii=False))
            print('============================================')
            assert False, e
        # print('================================')
        # print(json.dumps(data, indent = 2, ensure_ascii = False))
        # print('============================================')
        response = await client.post(f'{prefix}/hierarchy', json=data)
        assert response.status_code in [200, 201], f'{response.text}'


async def test_create_warehouse_relation(
        authenticated_client_with_db, test_db_session, simple_router_list, complex_router_list
):
    from tests.data_factory.fake_generator import generate_test_data
    from app.support.warehouse.router import WarehouseRouter  # , Region, RegionCreate, RegionCreateRelation
    # source = simple_router_list + complex_router_list
    test_number = 10
    client = authenticated_client_with_db
    router = WarehouseRouter()
    schema = router.create_schema_relation
    adapter = TypeAdapter(schema)
    prefix = router.prefix
    test_data = generate_test_data(
        schema, test_number, {'int_range': (1, test_number), 'decimal_range': (0.5, 1), 'float_range': (0.1, 1.0),
                              # 'field_overrides': {'name': 'Special Product'},
                              'faker_seed': 42}
    )
    for data in test_data:
        try:
            json_data = json.dumps(data)
            adapter.validate_json(json_data)
        except Exception as e:
            assert False, e

        response = await client.post(f'{prefix}/hierarchy', json=data)
        assert response.status_code in [200, 201], f'{response.text}'


async def test_create_item_relation(
        authenticated_client_with_db, test_db_session, simple_router_list, complex_router_list
):
    from tests.data_factory.fake_generator import generate_test_data
    from app.support.item.router import ItemRouter  # , Region, RegionCreate, RegionCreateRelation
    # source = simple_router_list + complex_router_list
    test_number = 1
    client = authenticated_client_with_db
    router = ItemRouter()
    schema = router.create_schema_relation
    adapter = TypeAdapter(schema)
    prefix = router.prefix
    test_data = generate_test_data(
        schema, test_number, {'int_range': (1, test_number), 'decimal_range': (0.5, 1), 'float_range': (0.1, 1.0),
                              # 'field_overrides': {'name': 'Special Product'},
                              'faker_seed': 42}
    )
    data = {
        "drink": {
            "category": {
                "name": "string",
                "description": "string",
                "description_ru": "string",
                "description_fr": "string",
                "name_ru": "string",
                "name_fr": "string"
            },
            "color": {
                "name": "string",
                "description": "string",
                "description_ru": "string",
                "description_fr": "string",
                "name_ru": "string",
                "name_fr": "string"
            },
            "sweetness": {
                "name": "string",
                "description": "string",
                "description_ru": "string",
                "description_fr": "string",
                "name_ru": "string",
                "name_fr": "string"
            },
            "subregion": {
                "region": {
                    "country": {
                        "name": "string",
                        "description": "string",
                        "description_ru": "string",
                        "description_fr": "string",
                        "name_ru": "string",
                        "name_fr": "string"
                    },
                    "name": "string",
                    "description": "string",
                    "description_ru": "string",
                    "description_fr": "string",
                    "name_ru": "string",
                    "name_fr": "string"
                },
                "name": "string",
                "description": "string",
                "description_ru": "string",
                "description_fr": "string",
                "name_ru": "string",
                "name_fr": "string"
            },
            "title": "string",
            "title_native": "string",
            "subtitle_native": "string",
            "subtitle": "string",
            "alc": 0,
            "sugar": 0,
            "aging": 0,
            "sparkling": False,
            "foods": [
                {
                    "name": "string",
                    "description": "string",
                    "description_ru": "string",
                    "description_fr": "string",
                    "name_ru": "string",
                    "name_fr": "string"
                }
            ],
            "varietals": [
                {
                    "varietal": {
                        "name": "string",
                        "description": "string",
                        "description_ru": "string",
                        "description_fr": "string",
                        "name_ru": "string",
                        "name_fr": "string"
                    },
                    "percentage": 0,
                    "additionalProp1": {}
                }
            ],
            "description": "string",
            "description_ru": "string",
            "description_fr": "string"
        },
        "warehouse": {
            "customer": {
                "login": "string",
                "firstname": "string",
                "lastname": "string",
                "account": "string"
            },
            "name": "string",
            "description": "string",
            "description_ru": "string",
            "description_fr": "string",
            "name_ru": "string",
            "name_fr": "string"
        },
        "volume": 0,
        "price": 0,
        "count": 0
    }

    for data1 in test_data:
        try:
            json_data = json.dumps(data)
            adapter.validate_json(json_data)
            _ = schema(**data)
        except Exception as e:
            assert False, e

        response = await client.post(f'{prefix}/hierarchy', json=data)
        assert response.status_code in [200, 201], f'{response.text}'


async def test_real_data_relation(authenticated_client_with_db, test_db_session, import_data):
    """ импорт данных из файла data.json через api
        падает по середине
    """
    from app.support.drink.router import DrinkRouter as Router
    client = authenticated_client_with_db
    dataset = import_data
    router = Router()
    schema = router.create_schema_relation
    adapter = TypeAdapter(schema)
    prefix = router.prefix
    for n, data in enumerate(dataset):
        if n < 7:
            continue
        if n == 15:
            break
        try:
            json_data = json.dumps(data)
            adapter.validate_json(json_data)
            assert True
        except Exception as e:
            # jprint(data)
            assert False, e
        try:
            response = await client.post(f'{prefix}/hierarchy', json=data)
            assert response.status_code in [200, 201], f'{prefix}, {response.text}'
        except Exception as e:
            jprint(data)
            assert False, f'{e} {response.status_code} {prefix=}, {response.text}'


async def test_upload_all_images(authenticated_client_with_db, test_db_session):
    """
        очень долгий тест 2-3 мин в зависимости от кол-ва картинок
        загрузка рисунков в базу данных
        без изменения имени
        с удалением фона
        size alignment
        direct (avoid api)
    """
    client = authenticated_client_with_db
    prefix = 'mongodb/images/direct'
    response = await client.post(prefix)
    assert response.status_code == 200, response.text


async def test_upload_json_data(authenticated_client_with_db, test_db_session):
    """
        импорт json_data в postgresql
        выполнять после test_upload_all_images
    """
    client = authenticated_client_with_db
    prefix = '/drinks/direct'
    response = await client.post(prefix)
    assert response.status_code == 200, response
