# tests/tests_crud/test_create.py
"""
    проверка методов post c валидацией входящих и исходящих данных
    отключены роутеры /items/hierarchy & /drinks/hierarchy - дает ошибку валидации - проверить и отремонтировать
    все отклюенные роутеры см conftest.py::exclude_routers
"""
import pytest
from rich.progress import track
from rich.console import Console
from rich.table import Table
from tests.data_factory.fake_generator import generate_test_data
from tests.conftest import get_model_by_name
pytestmark = pytest.mark.asyncio

# test_number -
test_number = 5


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
    fault_nmbr = 0
    good_nmbr = 0
    no_model = 0
    try:
        for route in track(source[::-1], description='test_generate_input_data'):
            # response_model = route.response_model  #
            request_model_name = route.openapi_extra.get('x-request-schema')
            # входная модель - по ней генерируются данные
            request_model = get_model_by_name(request_model_name)
            path = route.path
            if not request_model:
                table.add_row(path, fault, None, 'route has no request model')
                no_model += 1
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
                continue
            table.add_row(path, good, request_model_name)
            good_nmbr += 1
    except Exception as e:
        table.add_row(path, fault, request_model_name if request_model_name else None,
                      f'{e}')
    finally:
        print()
        console.print(table)
        table2 = Table(title="SUMMARY GENERATE INPUT DATA")
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
    fault_nmbr = 0
    good_nmbr = 0

    for n, route in enumerate(track(source[::-1], description='test_validate_input_data')):
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
                    continue
            else:
                table.add_row(path, good, request_model_name, None)
        except Exception as e:
            table.add_row(path, fault, request_model_name, f'{e}')
    print()
    console.print(table)
    table2 = Table(title="SUMMARY VALIDATE INPUT DATA")
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
    fault_nmbr = 0
    good_nmbr = 0
    for n, route in enumerate(track(source[::-1], description='test_create_routers')):
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
                                            'decimal_range': (0.01, 10),
                                            'float_range': (0.01, 100.0),
                                            # 'field_overrides': {'name': 'Special Product'},
                                            'faker_seed': 42}
                                           )
            if not test_data:
                fault_nmbr += 1
                table.add_row(path, fault, request_model_name, 'test_data was not generated.')
                continue
            for m, data in enumerate(test_data):
                try:        # запрос
                    response = await client.post(path, json=data)
                    if response.status_code in [200, 201]:
                        good_nmbr += 1
                    else:
                        print(f'=============={response.status_code} {response.text}')
                        for key, val in data.items():
                            print(f'         {key}: {val}')
                        print('==============')
                        raise Exception(f'{response.status_code}, {response.text}, {request_model_name}')
                except Exception as e:
                    fault_nmbr += 1
                    table.add_row(path, fault, request_model_name, f'{e}')
                    continue
            else:
                table.add_row(path, good, request_model_name, None)
        except Exception as e:
            table.add_row(path, fault, request_model_name, f'{e}')

    console.print(table)
    table2 = Table(title="SUMMARY CREATE DATA")
    table2.add_column("STATEMENT", style="cyan", no_wrap=True)
    table2.add_column("NUMBERS", justify="center", style="black")
    table2.add_row("total number of routes", f"{good_nmbr // test_number + fault_nmbr // test_number}")
    table2.add_row("number of good routes", f"{good_nmbr // test_number}")
    table2.add_row("number of fault routes", f"{fault_nmbr // test_number}")
    console.print(table2)
    if fault_nmbr > 0:
        assert False
