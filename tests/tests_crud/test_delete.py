# tests/tests_crud/test_delete.py
"""
    тестируем все методы GET и DELETE ()
    новые методы добавляются автоматически
    mongodb relation routes aare avoided due to scope function of mongodb client. see tests for mongodb only
"""

import pytest
from rich.console import Console
from rich.table import Table
from rich.progress import track
from tests.conftest import get_model_by_name
from tests.data_factory.fake_generator import generate_test_data

pytestmark = pytest.mark.asyncio

good = "✅"
fault = "❌"


test_number = 5


@pytest.mark.skip
async def test_delete_routers(authenticated_client_with_db, get_del_routes):
    console = Console()

    table = Table(title="Отчет по тестированию роутов DELETE")

    table.add_column("ROUTE", style="cyan", no_wrap=True)
    table.add_column("статус", justify="center", style="magenta")
    table.add_column('error', justify="left", style="red")

    source = get_del_routes
    client = authenticated_client_with_db
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    for n, route in enumerate(track(source, description='test_delete_router')):
        try:
            path = route.path
            if 'mongodb' in path or 'items' in path:
                continue
                # вынести в отдельнй тест так как mongodb session закрывается после каждого теста
                get_path = '/mongodb/imageslist'
            else:
                get_path = f"{path.replace('/delete', '').replace('{id}', '')}all"
            # получение списка id
            response = await client.get(get_path)
            if response.status_code in [200, 201]:
                result = response.json()
                if 'mongodb' in path:
                    continue
                    # ids = list(result.values())
                else:
                    # список id существующих
                    ids = [val.get('id') for val in result]
                # id = ids[-1]    # последняя запись
                # path = route.path.replace('{id}', f'{id}')
                # response = await client.delete(path)
                # if response.status_code in [200, 201]:
                #    table.add_row(path, good, None)
                m = 0
                for n, id in enumerate(reversed(ids)):   # перебор записей пока не удалятся все
                    path = route.path.replace('{id}', f'{id}')
                    response = await client.delete(path)
                    if response.status_code in [200, 201]:
                        m += 1
                        # table.add_row(path, good, None)
                    else:
                        table.add_row(path, fault, f'{response.status_code}: {response.text}')
                # else:
                table.add_row(path, good if m == n + 1 else fault, f'удалено {m} из {n + 1} записей')

                """
            else:
                table.add_row(path, fault, f'{response.status_code}. {response.text}')
                fault_nmbr += 1
                result[path] = f'{response.status_code}'
                """
        except Exception as e:
            table.add_row(path, good, f'{e}')
    console.print(table)
    table2 = Table(title="SUMMARY DELETE")
    table2.add_column("STATEMENT", style="cyan", no_wrap=True)
    table2.add_column("NUMBERS", justify="center", style="black")
    table2.add_row("total number of routes", f"{good_nmbr + fault_nmbr}")
    table2.add_row("number of good routes", f"{good_nmbr}")
    table2.add_row("number of fault routes", f"{fault_nmbr}")
    console.print(table2)
    if fault_nmbr > 0:
        assert False


@pytest.mark.skip
async def test_create_routers(authenticated_client_with_db, get_post_routes):
    console = Console()

    table = Table(title="Отчет по валидации сгенерированных данных для роутов CREATE № 2")
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
                                           {'int_range': (1, test_number - 1),
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
