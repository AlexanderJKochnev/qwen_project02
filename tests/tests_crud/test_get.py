# tests/test_routers.py
"""
    тестируем все роуты GET
    новые методы добавляются автоматически
"""

import pytest

from rich.console import Console
from rich.table import Table
from rich.progress import track

pytestmark = pytest.mark.asyncio


good = "✅"
fault = "❌"


async def test_get_routers(authenticated_client_with_db, get_get_routes):
    console = Console()

    table = Table(title="Отчет по тестированию роутов GET")

    table.add_column("ROUTE", style="cyan", no_wrap=True)
    table.add_column("статус", justify="center", style="magenta")
    table.add_column('error', justify="left", style="red")
    source = get_get_routes
    client = authenticated_client_with_db
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    for n, route in enumerate(track(source, description='test_get_routers')):
        try:
            path = route.path
            lang = 'en'
            id = "2"
            search = 'baro'
            # single = False
            if any((k in path for k in ('{file}', '{file_id}', '{filename}'))):
                continue
            if '{id}' in path:
                # single = True
                path = route.path.replace('{id}', f'{id}')
            if '{lang}' in path:
                path = path.replace('{lang}', f'{lang}')
            # if path.endswith('search') or path.endswith('search_all'):
            if path.endswith('search'):
                path = f'{path}?search={search}&page=1&page_size=20'
            if path.endswith('search_all'):
                path = f'{path}?search={search}'
            if 'search_by_drink' in path:
                path = f'{path}?search={search}&page=1&page_size=20'
            if 'search_trigram' in path:
                path = f'{path}?search_str={search}&page=1&page_size=15'

            # if any((path.endswith('{file}'), path.endswith('{file_id}'), path.endswith('{filename}'))):
            #     continue

            response = await client.get(path)
            if response.status_code in [200, 201]:
                table.add_row(path, good, None)
                good_nmbr += 1
            else:
                table.add_row(path, fault, f"{response.status_code} {response.text}")
                fault_nmbr += 1
                result[path] = f'{response.status_code}'
        except Exception as e:
            table.add_row(path, fault, f"{e}")
            # print(f'ОШИБКА {e}')
            fault_nmbr += 1
            result[f'{path}'] = e

    console.print(table)
    table2 = Table(title="SUMMARY GET RUTERS")
    table2.add_column("STATEMENT", style="cyan", no_wrap=True)
    table2.add_column("NUMBERS", justify="center", style="black")
    table2.add_row("total number of routes", f"{good_nmbr + fault_nmbr}")
    table2.add_row("number of good routes", f"{good_nmbr}")
    table2.add_row("number of fault routes", f"{fault_nmbr}")
    console.print(table2)
    if fault_nmbr > 0:
        assert False
