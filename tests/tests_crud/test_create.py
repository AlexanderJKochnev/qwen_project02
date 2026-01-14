# tests/test_create.py
"""
    проверка методов post c валидацией входящих и исходящих данных
    отключены роутеры /items/hierarchy & /drinks/hierarchy - дает ошибку валидации - проверить и отремонтировать
    все отклюенные роутеры см conftest.py::exclude_routers
"""
import pytest
from tqdm import tqdm
from rich.console import Console
from rich.table import Table
from app.core.utils.common_utils import jprint
from tests.utility.assertion import assertions
from tests.data_factory.fake_generator import generate_test_data
from tests.conftest import get_model_by_name
pytestmark = pytest.mark.asyncio

# test_number -
test_number = 10


good = "✅"
fault = "❌"


async def test_generate_input_data(authenticated_client_with_db, get_post_routes):
    console = Console()

    table = Table(title="Отчет по тестированию роутов CREATE")

    table.add_column("ROUTE", style="cyan", no_wrap=True)
    table.add_column("статус", justify="center", style="magenta")
    table.add_column("request model", justify="right", style="green")
    table.add_column('error', justify="right", style="red")

    source = get_post_routes
    # client = authenticated_client_with_db
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    no_model = 0
    try:
        for route in tqdm(source[::-1], desc=('перебираем роутеры')):
            # response_model = route.response_model  #
            request_model_name = route.openapi_extra.get('x-request-schema')
            # входная модель - по ней генерируются данные
            request_model = get_model_by_name(request_model_name)
            path = route.path
            if not request_model:
                table.add_row(path, fault, None, 'route has no request model')
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
                table.add_row(path, fault, request_model_name, 'route has no request model')
                fault_nmbr += 1
                result[path] = 'test_data was not generated'
                continue
            table.add_row(path, good, request_model_name)
            good_nmbr += 1
    except Exception as e:
        table.add_row(path, fault, request_model_name if request_model_name else None,
                      f'{e}')
    finally:
        print()
        console.print(table)
        table2 = Table(title="SUMMARY")
        table2.add_column("STATEMENT", style="cyan", no_wrap=True)
        table2.add_column("NUMBERS", justify="center", style="black")
        table2.add_row("total number of routes", f"{good_nmbr + fault_nmbr + no_model}")
        table2.add_row("number of good routes", f"{good_nmbr}")
        table2.add_row("number of fault routes", f"{fault_nmbr}")
        table2.add_row("number of routes without response models", f"{no_model}")
        console.print(table2)


async def test_validate_input_data(authenticated_client_with_db, get_post_routes):
    console = Console()

    table = Table(title="Отчет по валидации сгенерированных данных для роутов CREATE")

    table.add_column("ROUTE", style="cyan", no_wrap=True)
    table.add_column("статус", justify="center", style="magenta")
    table.add_column("request model", justify="right", style="green")
    table.add_column('error', justify="right", style="red")
    source = get_post_routes
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0

    for n, route in enumerate(source[::-1]):
        try:
            # response_model = route.response_model  #
            request_model_name = route.openapi_extra.get('x-request-schema')
            # входная модель - по ней генерируются данные
            request_model = get_model_by_name(request_model_name)
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
                table.add_row(path, fault, request_model_name, 'test_data was not generated')
                fault_nmbr += 1
                result[path] = 'test_data was not generated'
                continue
            for m, data in enumerate(test_data):
                try:        # валидация исходных данных (проверка генератора тестовых данных)
                    py_model = request_model(**data)
                    rev_dict = py_model.model_dump()
                    if rev_dict != data:
                        raise Exception('исходные данные не совпадают с валидированными')
                    # table.add_row(path, good, request_model_name, None)
                    good_nmbr += 1
                    # assert data == rev_dict, f'pydantic validation fault {prefix}'
                except Exception as e:
                    table.add_row(path, fault, request_model_name, f'{e}')
                    fault_nmbr += 1
                    result[path] = f'test_data was generated incorrectly: {e}'
                    continue
            else:
                table.add_row(path, good, request_model_name, None)
        except Exception as e:
            table.add_row(path, fault, request_model_name, f'{e}')
    print()
    console.print(table)
    table2 = Table(title="SUMMARY")
    table2.add_column("STATEMENT", style="cyan", no_wrap=True)
    table2.add_column("NUMBERS", justify="center", style="black")
    table2.add_row("total number of routes", f"{good_nmbr // test_number + fault_nmbr // test_number}")
    table2.add_row("number of good routes", f"{good_nmbr // test_number}")
    table2.add_row("number of fault routes", f"{fault_nmbr // test_number}")
    console.print(table2)


async def test_create_routers(authenticated_client_with_db, get_post_routes):
    console = Console()

    table = Table(title="Отчет по валидации сгенерированных данных для роутов CREATE")
    table.add_column("ROUTE", style="cyan", no_wrap=True)
    table.add_column("статус", justify="center", style="magenta")
    table.add_column("request model", justify="right", style="green")
    table.add_column('error', justify="right", style="red")
    source = get_post_routes
    client = authenticated_client_with_db
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    for n, route in tqdm(enumerate(source[::-1]), desc=('перебираем роутеры')):
        try:
            # response_model = route.response_model  #
            request_model_name = route.openapi_extra.get('x-request-schema')
            # входная модель - по ней генерируются данные
            request_model = get_model_by_name(request_model_name)
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
                result[path] = f'test_data was not generated. {request_model_name}'
                continue
            for m, data in enumerate(test_data):
                try:        # запрос
                    response = await client.post(path, json=data)
                    if response.status_code in [200, 201]:
                        good_nmbr += 1
                    else:
                        print('==============')
                        for key, val in data.items():
                            print(f'         {key}: {val}')
                        print('==============')
                        raise Exception(f'{response.status_code}, {response.text}, {request_model_name}')
                except Exception as e:
                    fault_nmbr += 1
                    result[path] = f'{e}'
                    continue
            else:
                table.add_row(path, good, request_model_name, None)
        except Exception as e:
            table.add_row(path, fault, request_model_name, f'{e}')

    console.print(table)
    table2 = Table(title="SUMMARY CREATE")
    table2.add_column("STATEMENT", style="cyan", no_wrap=True)
    table2.add_column("NUMBERS", justify="center", style="black")
    table2.add_row("total number of routes", f"{good_nmbr // test_number + fault_nmbr // test_number}")
    table2.add_row("number of good routes", f"{good_nmbr // test_number}")
    table2.add_row("number of fault routes", f"{fault_nmbr // test_number}")
    console.print(table2)
    if fault_nmbr > 0:
        assert False


@pytest.mark.skip
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


@pytest.mark.skip
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


@pytest.mark.skip
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


@pytest.mark.skip
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
