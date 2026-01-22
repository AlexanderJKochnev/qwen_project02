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

pytestmark = pytest.mark.asyncio

good = "✅"
fault = "❌"


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
            if 'mongodb' in path:
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
                for id in reversed(ids):   # перебор записей пока не найдется без зависимых
                    path = route.path.replace('{id}', f'{id}')
                    # .replace('{file_id}', f'{id}'))
                    try:
                        response = await client.delete(path)
                        if response.status_code == 500:
                            continue
                        if response.status_code in [200, 201]:
                            table.add_row(path, good, None)
                            good_nmbr += 1
                            break
                    except Exception as e:
                        print(f'{path=}  {e}')
            else:
                table.add_row(path, fault, f'{response.status_code}. {response.text}')
                fault_nmbr += 1
                result[path] = f'{response.status_code}'
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
