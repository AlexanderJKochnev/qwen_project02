# tests/test_create.py
"""
    проверка методов post c валидацией входящих и исходящих данных
    эта группа тестов падает если запускать их вместе с другими тесатми - очередность не важна
    разобраться
"""
import pytest
from app.core.utils.common_utils import jprint
from tests.utility.assertion import assertions
from tests.data_factory.fake_generator import generate_test_data

pytestmark = pytest.mark.asyncio


test_number = 5


async def test_generate_input_data(authenticated_client_with_db, get_post_routes):
    source = get_post_routes
    # client = authenticated_client_with_db
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    no_model = 0
    try:
        for n, route in enumerate(source[::-1]):
            # response_model = route.response_model  #
            request_model = route.openapi_extra.get('request_model')  # входная модель - по ней генерируются данные
            path = route.path
            if not request_model:
                no_model += 1
                result[path] = 'test_data has no request model'
                continue
            test_data = generate_test_data(request_model, test_number,
                                           {'int_range': (1, test_number),
                                            'decimal_range': (0.5, 1),
                                            'float_range': (0.1, 1.0),
                                            # 'field_overrides': {'name': 'Special Product'},
                                            'faker_seed': 42}
                                           )
            if not test_data:
                fault_nmbr += 1
                result[path] = 'test_data was not generated'
                continue
            good_nmbr += 1
    except Exception as e:
        print(path)
        print(f'ОШИБКА {e}')
    result['good'] = good_nmbr
    result['fault'] = fault_nmbr
    if fault_nmbr > 0:
        for key, val in result.items():
            print(f'{key}: {val if isinstance(val, int) else val[0:15]}')
        assert False, f'выявлено {fault_nmbr} ошибок'
    else:
        print(f'{good_nmbr} routers tested OK')
        print(f'{no_model} routers have no request_model')
        for key, val in result.items():
            print(f'    {key}: {val}')
        assert True


async def test_validate_input_data(authenticated_client_with_db, get_post_routes):
    source = get_post_routes
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    try:
        for n, route in enumerate(source[::-1]):
            # response_model = route.response_model  #
            request_model = route.openapi_extra.get('request_model')  # входная модель - по ней генерируются данные
            path = route.path
            if not request_model:       # пропускаем роуты без request_model
                continue
            # генерация данных
            test_data = generate_test_data(request_model, test_number,
                                           {'int_range': (1, test_number),
                                            'decimal_range': (0.5, 1),
                                            'float_range': (0.1, 1.0),
                                            # 'field_overrides': {'name': 'Special Product'},
                                            'faker_seed': 42}
                                           )
            if not test_data:
                fault_nmbr += 1
                result[path] = 'test_data was not generated'
                continue
            for m, data in enumerate(test_data):
                try:        # валидация исходных данных (проверка генератора тестовых данных)
                    py_model = request_model(**data)
                    rev_dict = py_model.model_dump()
                    if rev_dict != data:
                        raise Exception('исходные данные не совпадают с валидированными')
                    good_nmbr += 1
                    # assert data == rev_dict, f'pydantic validation fault {prefix}'
                except Exception as e:
                    fault_nmbr += 1
                    result[path] = f'test_data was generated incorrectly: {e}'
                    continue
    except Exception as e:
        print(path)
        print(f'ОШИБКА {e}')
    result['good'] = good_nmbr // test_number
    result['fault'] = fault_nmbr // test_number
    if fault_nmbr > 0:
        for key, val in result.items():
            print(f'{key}: {val if isinstance(val, int) else val[0:15]}')
        assert False, f'выявлено {fault_nmbr} ошибок'
    else:
        print(f'{good_nmbr // test_number} routers tested OK')
        print(f'{fault_nmbr // test_number} routers test failed')
        for key, val in result.items():
            print(f'    {key}: {val}')
        assert True


async def test_create_routers(authenticated_client_with_db, get_post_routes):
    source = get_post_routes
    client = authenticated_client_with_db
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    try:
        for n, route in enumerate(source[::-1]):
            # response_model = route.response_model  #
            request_model = route.openapi_extra.get('request_model')  # входная модель - по ней генерируются данные
            path = route.path
            if not request_model:       # пропускаем роуты без request_model
                continue
            # генерация данных
            test_data = generate_test_data(request_model, test_number,
                                           {'int_range': (1, test_number),
                                            'decimal_range': (0.5, 1),
                                            'float_range': (0.1, 1.0),
                                            # 'field_overrides': {'name': 'Special Product'},
                                            'faker_seed': 42}
                                           )
            if not test_data:
                fault_nmbr += 1
                result[path] = 'test_data was not generated'
                continue
            for m, data in enumerate(test_data):
                try:        # запрос
                    response = await client.post(path, json=data)
                    if response.status_code in [200, 201]:
                        good_nmbr += 1
                    else:
                        raise Exception(f'{response.status_code}, {response.text}')
                except Exception as e:
                    fault_nmbr += 1
                    result[path] = f'{e}'
                    continue
    except Exception as e:
        print(path)
        print(f'ОШИБКА {e}')
    result['good'] = good_nmbr // test_number
    result['fault'] = fault_nmbr // test_number
    if fault_nmbr > 0:
        for key, val in result.items():
            print(f'{key}: {val if isinstance(val, int) else val}')
            print('----------------------------')
        assert False, f'выявлено {fault_nmbr // test_number} ошибок'
    else:
        print(f'{good_nmbr // test_number} routers tested OK')
        print(f'{fault_nmbr // test_number} routers test failed')
        for key, val in result.items():
            print(f'    {key}: {val}')
        assert True


async def test_new_data_generator(authenticated_client_with_db, test_db_session,
                                  simple_router_list, complex_router_list):
    """ валидация генерируемых данных и загрузка """
    from tests.data_factory.fake_generator import generate_test_data
    source = simple_router_list + complex_router_list
    client = authenticated_client_with_db
    for n, item in enumerate(source):
        router = item()
        schema = router.create_schema
        model = router.model
        # adapter = TypeAdapter(schema)
        prefix = router.prefix
        test_data = generate_test_data(
            schema, test_number,
            {'int_range': (1, test_number),
             'decimal_range': (0.5, 1),
             'float_range': (0.1, 1.0),
             # 'field_overrides': {'name': 'Special Product'},
             'faker_seed': 42}
        )
        if not test_data:
            assert False, f'create_schema is model {model} '
        for m, data in enumerate(test_data):
            try:
                # валидируем по Pydantic схеме
                py_model = schema(**data)
                rev_dict = py_model.model_dump()
                assert data == rev_dict, f'pydantic validation fault {prefix}'
            except Exception as e:
                print(f'first validation fault: {e}')
                jprint(data)
                assert False, f'first validation false {prefix=}'
            try:
                # валидируем по Alchemy model
                if prefix not in ['/drinks']:
                    al_model = model(**data)
                    rev_dict = al_model.to_dict()
                    for key in ['updated_at', 'id', 'created_at']:
                        rev_dict.pop(key, None)
                    assert data == rev_dict, f'alchemy validation fault {prefix} '
            except Exception as e:
                print(f'second validation fault: {e}')
                jprint(data)
                assert False, f'second validation false {prefix=}'
            try:
                response = await client.post(f'{prefix}', json=data)
                assert response.status_code in [200, 201], f'{prefix}, {response.text}'
            except Exception as e:
                print(prefix, f'last error: {e}')
                jprint(data)
                assert False, f'{response.status_code=} {prefix=}, error: {e}, example {m}, {response.text}'


async def test_new_data_generator_relation_validation(simple_router_list, complex_router_list):
    """
        валидация генерируемых данных со связанныим полями
    """
    import json
    from tests.data_factory.fake_generator import generate_test_data
    from pydantic import TypeAdapter
    failed_cases = []
    source = simple_router_list + complex_router_list
    for n, item in enumerate(source):
        router = item()
        schema = router.create_schema_relation
        adapter = TypeAdapter(schema)
        prefix = router.prefix
        print(f'{schema=}===={prefix=}====')
        test_data = generate_test_data(
            schema, test_number,
            {'int_range': (1, test_number),
             'decimal_range': (0.5, 1),
             'float_range': (0.1, 1.0),
             # 'field_overrides': {'name': 'Special Product'},
             'faker_seed': 42}
        )
        print(f'======================={test_data=}')
        for m, data in enumerate(test_data):
            try:
                _ = schema(**data)
                json_data = json.dumps(data)
                adapter.validate_json(json_data)
            except Exception as e:
                if assertions(False, failed_cases, item, prefix, f'ошибка валидации: {e}'):
                    continue  # Продолжаем со следующим роутером
        if failed_cases:
            pytest.fail("Failed routers:\n" + "\n".join(failed_cases))


async def test_new_data_generator_relation_correctness(simple_router_list, complex_router_list):
    """
        сравнивает сгенерированные данные и отвалидированные
        (валидация не должна изменять сгенерированные данные)
    """
    from tests.data_factory.fake_generator import generate_test_data
    failed_cases = []
    source = simple_router_list + complex_router_list
    for n, item in enumerate(source):
        router = item()
        schema = router.create_schema_relation
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
                model_data = schema(**data)
                assert data == model_data.model_dump()
            except Exception as e:
                if assertions(False, failed_cases, item, prefix, f'ошибка валидации: {e}'):
                    continue  # Продолжаем со следующим роутером
        if failed_cases:
            pytest.fail("Failed routers:\n" + "\n".join(failed_cases))


async def test_new_data_generator_relation(authenticated_client_with_db, test_db_session,
                                           simple_router_list, complex_router_list):
    """ валидация генерируемых данных со связанными полями и загрузка """
    from tests.data_factory.fake_generator import generate_test_data
    failed_cases = []
    source = simple_router_list + complex_router_list
    client = authenticated_client_with_db
    for n, item in enumerate(source):
        router = item()
        schema = router.create_schema_relation
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
            # валидация
            try:
                _ = schema(**data)
            except Exception as e:
                if assertions(False, failed_cases, item, prefix, f'ошибка валидации: {e}'):
                    continue  # Продолжаем со следующим роутером
            # запись валидированных данных
            try:
                response = await client.post(f'{prefix}/hierarchy', json=data)
                if response.status_code != 200:
                    print(prefix)
                    jprint(data)
                assert response.status_code == 200, response.text
            except Exception as e:
                print(f'{response.text=}')
                print(f'{prefix=},  {e=}')
                jprint(data)
                print('------------------------------------------------------')

    if failed_cases:
        pytest.fail("Failed routers:" + "\n".join(failed_cases))
