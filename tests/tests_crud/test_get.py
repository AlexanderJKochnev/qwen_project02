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
    fault_nmbr = 0
    good_nmbr = 0
    for n, route in enumerate(track(source, description='test_get_routers')):
        try:
            path = route.path
            lang = 'en'
            id = "2"
            search = 'baro'
            # single = False
            if any((k in path for k in ('{file}', '{file_id}', '{filename}', 'search'))):
                continue
            if '{id}' in path:
                path = route.path.replace('{id}', f'{id}')
            if '{lang}' in path:
                path = path.replace('{lang}', f'{lang}')
            if path.endswith('search'):
                path = f'{path}?search={search}&page=1&page_size=20'
            if path.endswith('search_geans'):
                path = f'{path}?search_geans={search}&page=1&page_size=20'
            if path.endswith('search_all') or path.endswith('search_geans_all'):
                path = f'{path}?search_all={search}'
            if path.endswith('search_geans_all'):
                path = f'{path}?search_geans_all={search}'
            if 'search_by_drink' in path:
                path = f'{path}?search={search}&page=1&page_size=20'
            if 'search_trigram' in path:
                path = f'{path}?search_str={search}&page=1&page_size=15'
            if path in ['/detail/en/2', '/api/2']:  # '/api/all']
                path = path.replace('2', '3')
            response = await client.get(path)
            if response.status_code in [200, 201]:
                table.add_row(path, good, None)
                good_nmbr += 1
            else:
                if path.endswith((f'image/{id}', f'image_png/{id}', f'thumbnail/{id}', f'thumbnail_png/{id}')):
                    table.add_row(path, good, f"{response.status_code} {response.text}")
                else:
                    table.add_row(path, fault, f"{response.status_code} {response.text}")
                    fault_nmbr += 1
        except Exception as e:
            table.add_row(path, fault, f"common error {path} {response.status_code=} {e}")
            # print(f'ОШИБКА {e}')
            fault_nmbr += 1

    console.print(table)
    table2 = Table(title="SUMMARY GET ROUTERS")
    table2.add_column("STATEMENT", style="cyan", no_wrap=True)
    table2.add_column("NUMBERS", justify="center", style="black")
    table2.add_row("total number of routes", f"{good_nmbr + fault_nmbr}")
    table2.add_row("number of good routes", f"{good_nmbr}")
    table2.add_row("number of fault routes", f"{fault_nmbr}")
    console.print(table2)
    if fault_nmbr > 0:
        assert False


async def test_search_routers(authenticated_client_with_db, get_get_routes):
    console = Console()

    table = Table(title="Отчет по тестированию роутов GET SEARCH")

    table.add_column("ROUTE", style="cyan", no_wrap=True)
    table.add_column("статус", justify="center", style="magenta")
    table.add_column('error', justify="left", style="red")
    source = get_get_routes
    client = authenticated_client_with_db
    fault_nmbr = 0
    good_nmbr = 0
    for n, route in enumerate(track(source, description='test_get_routers')):
        if 'search' not in route.path:
            continue
        try:
            path = route.path
            lang = 'en'
            # id = "2"
            search = 'baro'
            empty = None
            # single = False
            if '{lang}' in path:
                path = path.replace('{lang}', f'{lang}')
            if path.endswith('search'):
                path = f'{path}?search={search}&page=1&page_size=20'
                path2 = f'{path}?search={empty}&page=1&page_size=20'
            if path.endswith('search_geans'):
                path = f'{path}?search_geans={search}&page=1&page_size=20'
                path2 = f'{path}?search_geans={empty}&page=1&page_size=20'
            if path.endswith('search_all') or path.endswith('search_geans_all'):
                path = f'{path}?search_all={search}'
                path2 = f'{path}?search_all={empty}'
            if path.endswith('search_geans_all'):
                path = f'{path}?search_geans_all={search}'
                path2 = f'{path}?search_geans_all={empty}'
            if 'search_by_drink' in path:
                path = f'{path}?search={search}&page=1&page_size=20'
                path2 = f'{path}?search={empty}&page=1&page_size=20'
            if 'search_trigram' in path:
                path = f'{path}?search_str={search}&page=1&page_size=15'
                path2 = f'{path}?search_str={empty}&page=1&page_size=15'
            for n, k in enumerate((path, path2)):
                response = await client.get(k)
                if response.status_code in [200, 201]:
                    good_nmbr += 1
                    tmp = response.json()
                    if isinstance(tmp, dict):
                        if len(tmp.get('items')) <= tmp.get('total'):
                            res = good
                            detail = None
                        else:
                            res = fault
                            detail = f"total = tmp.get('total'), items nmrb {len(tmp.get('items'))}"
                    else:
                        res = good
                        detail = None
                    table.add_row(k, res, detail)
                else:
                    table.add_row(k, fault, f"{response.status_code} {response.text}")
                    fault_nmbr += 1
        except Exception as e:
            table.add_row(path, fault, f"common error {path} {response.status_code=} {e}")
            # print(f'ОШИБКА {e}')
            fault_nmbr += 1

    console.print(table)
    table2 = Table(title="SUMMARY SEARCH ROUTERS")
    table2.add_column("STATEMENT", style="cyan", no_wrap=True)
    table2.add_column("NUMBERS", justify="center", style="black")
    table2.add_row("total number of routes", f"{good_nmbr + fault_nmbr}")
    table2.add_row("number of good routes", f"{good_nmbr}")
    table2.add_row("number of fault routes", f"{fault_nmbr}")
    console.print(table2)
    if fault_nmbr > 0:
        assert False
