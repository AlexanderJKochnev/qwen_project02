# tests/test_delete.py
"""
    тестируем все методы POST и DELETE ()
    новые методы добавляются автоматически
    pytest tests/test_delete.py --tb=auto --disable-warnings -vv --capture=no
"""

import pytest


pytestmark = pytest.mark.asyncio


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
