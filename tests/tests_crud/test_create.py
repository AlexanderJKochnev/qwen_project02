# tests/test_create.py
"""
    проверка методов post c валидацией входящих и исходящих данных
    эта группа тестов падает если запускать их вместе с другими тесатми - очередность не важна
    разобраться
"""
import pytest
from app.core.utils.common_utils import jprint
from tests.utility.assertion import assertions
pytestmark = pytest.mark.asyncio


test_number = 5


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
