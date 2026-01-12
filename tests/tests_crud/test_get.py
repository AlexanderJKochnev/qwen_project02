# tests/test_routers.py
"""
    тестируем все роуты GET
    новые методы добавляются автоматически
"""

import pytest

from app.core.schemas.base import PaginatedResponse


pytestmark = pytest.mark.asyncio


async def test_get_routers(authenticated_client_with_db, get_get_routes):
    source = get_get_routes
    client = authenticated_client_with_db
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    for n, route in enumerate(source):
        try:
            path = route.path
            lang = 'en'
            id = "2"
            search = 'vi'
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
                good_nmbr += 1
            else:
                fault_nmbr += 1
                result[path] = f'{response.status_code}'
        except Exception as e:
            # print(f'ОШИБКА {e}')
            fault_nmbr += 1
            result[f'{path}'] = e
    result['good'] = good_nmbr
    result['fault'] = fault_nmbr
    print(f'{good_nmbr} routers tested OK')
    print(f'{fault_nmbr} routers test failed')
    for key, val in result.items():
        print(f'    {key}: {val}')
        print('------------------')
    if fault_nmbr > 0:
        assert False, f'{fault_nmbr} ошибок'


@pytest.mark.skip
async def test_get_all(authenticated_client_with_db, test_db_session,
                       simple_router_list, complex_router_list, fakedata_generator):
    """ тестирует методы get all - с проверкой формата ответа """
    failed_cases = []
    # routers = routers_get_all
    routers = simple_router_list + complex_router_list
    expected_response = PaginatedResponse.model_fields.keys()
    client = authenticated_client_with_db
    for router_class in reversed(routers):
        router = router_class()
        prefix = router.prefix
        response = await client.get(f'{prefix}')
        if response.status_code != 200:
            error_info = f'{router_class.__name__}: {prefix}, status: {response.status_code}, text: {response.text}'
            failed_cases.append(error_info)
            print(f"FAILED: {error_info}")  # Выводим сразу для информации
            continue  # Продолжаем со следующим роутером
        # assert response.status_code == 200, f'метод GET не работает для пути "{prefix}"'
        assert response.json().keys() == expected_response, \
            f'метод GET для пути "{prefix}" возвращает некорректные данные'
    if failed_cases:
        pytest.fail("Failed routers:\n" + "\n".join(failed_cases))


@pytest.mark.skip
async def test_get_nopage(authenticated_client_with_db, test_db_session, routers_get_all, fakedata_generator):
    """ тестирует методы get all - с проверкой формата ответа """
    routers = routers_get_all
    # expected_response = ListResponse.model_fields.keys()
    client = authenticated_client_with_db
    for prefix in routers:
        if prefix in ['/api']:  # api не имеет метода all, удалить когда заведется
            continue
        response = await client.get(f'{prefix}/all')
        assert response.status_code == 200, response.text


@pytest.mark.skip
async def test_get_one(authenticated_client_with_db, test_db_session,
                       routers_get_all, fakedata_generator):
    """ тестирует методы get one - c проверкой id """
    from app.core.utils.common_utils import jprint
    client = authenticated_client_with_db
    routers = routers_get_all

    for prefix in routers:
        if 'items' in prefix:
            continue
        response = await client.get(f'{prefix}/1')
        assert response.status_code in [200], response.text
        if 'subcategories' in prefix:
            result = response.json()
            jprint(result)


@pytest.mark.skip
async def test_fault_get_one(authenticated_client_with_db, test_db_session,
                             routers_get_all, fakedata_generator):
    """ тестирует методы get one - несуществующий id """
    client = authenticated_client_with_db
    routers = routers_get_all
    for prefix in routers:
        id = 1000
        response = await client.get(f'{prefix}/{id}')
        assert response.status_code == 404
        # error_data = response.json()
        # assert "detail" in error_data
        # assert "not found" in error_data["detail"].lower(), response.text


@pytest.mark.skip
async def test_get_one_items(authenticated_client_with_db, test_db_session,
                             simple_router_list, complex_router_list,
                             fakedata_generator):
    from app.support.item.router import ItemRouter as Router
    # from app.support.drink.router import DrinkRouter as Router
    # router_list = simple_router_list + complex_router_list
    router_list = [Router]
    for item in router_list:
        router = item()
        prefix = router.prefix
        client = authenticated_client_with_db
        id = 2
        response = await client.get(f'{prefix}/{id}')
        assert response.status_code == 200, f'{prefix}, {response.text}'
