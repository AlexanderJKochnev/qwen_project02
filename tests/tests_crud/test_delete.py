# tests/test_delete.py
"""
    тестируем все методы POST и DELETE ()
    новые методы добавляются автоматически
    ПОЧЕМУ ПРИ ТЕСТИРОВАНИИ УДАЛЯЮТСЯ ЗАПИСИ ИЗ ПОДЧИНЕННЫХ ТАБЛИЦ?
    ПРИ УДАЛЕНИИ ИЗ CATEGORY - УДАЛЯЮТСЯ ЗАВИСИМЫЕ ЗАПИСИ ИЗ SUBCATEGORY?
"""

import pytest
from rich.console import Console
from rich.table import Table

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
    for n, route in enumerate(source):
        try:
            path = route.path
            if 'mongodb' in path:
                continue
                # вынести в отдельнй тест так как mongodb session закрывается после каждого теста
                get_path = '/mongodb/imageslist'
            else:
                get_path = f'{path.replace('/delete', '').replace('{id}', '')}all'

            response = await client.get(get_path)
            if response.status_code in [200, 201]:
                result = response.json()
                if 'mongodb' in path:
                    continue
                    # ids = list(result.values())
                else:
                    ids = [val.get('id') for val in result]
                    # print(f'{get_path}...{ids=}')
                for id in ids:   # перебор записей пока не найдется без зависимых
                    if '/delete/sweetness' in route.path:
                        table.add_row(route.path, fault, f'{route.path}')
                        # print(f"==={route.path.replace('{id}', str(id))=}")
                        # print(f"{route.path=}")
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


@pytest.mark.skip
async def test_fault_delete(authenticated_client_with_db, test_db_session,
                            routers_get_all):
    """ тестирует методы DELETE  c проверкой id fault"""
    client = authenticated_client_with_db
    routers = routers_get_all
    for prefix in reversed(routers):
        if 'api' in prefix:     # в api нет метода delete - когдя пояявится - убрать
            continue
        id = 10000   # impossible id
        resp = await client.delete(f'{prefix}/{id}')
        assert resp.status_code == 404, f'{prefix} {resp.text}'


@pytest.mark.skip
async def test_fault_delete_foreign_violation(authenticated_client_with_db, test_db_session,
                                              simple_router_list, complex_router_list,
                                              fakedata_generator):
    """
        неудачное удаление due to foregn violation
        неудалчный тест - переделать - сначала найти запсиси с зависимостями потом попробовать их удалить
        и получитьь ошибку
    """
    from app.support.drink.router import DrinkRouter
    item = DrinkRouter
    router = item()
    prefix = router.prefix
    client = authenticated_client_with_db
    id = 1
    try:
        response = await client.delete(f'{prefix}/{id}')
        assert response.status_code == 200
    except Exception as e:
        assert False, e  # response.status_code == 200, f'{prefix}, {response.text}'


@pytest.mark.skip
async def test_delete(authenticated_client_with_db, test_db_session):  # fakedata_generator):
    """ тестирует методы DELETE c проверкой id
        удаление всех записей
    """
    from app.support.item.router import ItemRouter
    client = authenticated_client_with_db
    router = ItemRouter()
    prefix = router.prefix
    result = await client.get(f'{prefix}/all')
    assert result.status_code == 200, 'невозможно подсчитать кол-во записей'
    for instance in result.json():
        id = instance.get('id')
        response = await client.delete(f'{prefix}/{id}')
        if response.status_code != 200:
            print(f'ошибка удаления {prefix}')
        assert response.status_code == 200, f'ошибка удаления {prefix}/{id}'
        # проверка удаления
        check = await client.get(f'{prefix}/{id}')
        assert check.status_code in [404, 500], check.text
