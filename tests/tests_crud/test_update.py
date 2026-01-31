# tests/test_patch.py
"""
    тестируем все методы UPDATE ()
    новые методы добавляются автоматически
    pytest tests/test_patch.py --tb=auto --disable-warnings -vv --capture=no
"""
import pytest
from rich.console import Console
from rich.table import Table
from rich.progress import track

pytestmark = pytest.mark.asyncio

good = "✅"
fault = "❌"


async def test_patch_routers(authenticated_client_with_db, get_patch_routes):
    console = Console()

    table = Table(title="Отчет по тестированию роутов UPDATE")

    table.add_column("ROUTE", style="cyan", no_wrap=True)
    table.add_column("статус", justify="center", style="magenta")
    table.add_column('error', justify="left", style="red")

    source = get_patch_routes
    client = authenticated_client_with_db
    # result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    subj_fields = ('title', 'subtitle', 'name', 'description', 'image_id')
    for n, route in enumerate(track(source, description='test_update_routers')):
        try:
            # получаем список всех записей
            path = route.path
            get_path = f"{path.replace('/patch', '').replace('{id}', '')}all"
            response = await client.get(get_path)
            if response.status_code in [200, 201]:
                result = response.json()
                instance = result[-2]        # берем предпоследнюю запись
                id = instance.get('id')
                path = route.path.replace('{id}', f'{id}')
                if path.startswith('/items'):
                    updated_dict = {'count': 100, 'price': 0.1}
                elif path.startswith('/drink'):
                    updated_dict = {'title': 'TEST', 'subtitle': 'TEST'}
                else:
                    updated_dict = {key: f'UPDATED {val}' for key, val in instance.items()
                                    if any((key.startswith(subj) for subj in subj_fields))}
                response = await client.patch(path, json=updated_dict)

                if response.status_code in [200, 201]:
                    good_nmbr += 1
                    table.add_row(path, good, None)
                else:
                    fault_nmbr += 1
                    table.add_row(path, fault, f'{response.status_code} {response.text}')
                    # result[path] = f'{response.status_code}'
        except Exception as e:
            fault_nmbr += 1
            table.add_row(path, fault, f'ERROR: {e}')
    console.print(table)
    table2 = Table(title="SUMMARY UPDATE ROUTERS")
    table2.add_column("STATEMENT", style="cyan", no_wrap=True)
    table2.add_column("NUMBERS", justify="center", style="black")
    table2.add_row("total number of routes", f"{good_nmbr + fault_nmbr}")
    table2.add_row("number of good routes", f"{good_nmbr}")
    table2.add_row("number of fault routes", f"{fault_nmbr}")
    console.print(table2)
    if fault_nmbr > 0:
        assert False
