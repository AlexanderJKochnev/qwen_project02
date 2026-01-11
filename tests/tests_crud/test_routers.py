# tests/tests_crud/test_routers.py
"""
    compaire all routes and tested ones
"""
import pytest
# from app.core.utils.common_utils import jprint
# from tests.utility.assertion import assertions
pytestmark = pytest.mark.asyncio


def test_routers_no_request_model(get_all_routes):
    """
         выдает список рутов не имеющих request_model
    """
    # all_routers = simple_router_list + complex_router_list
    # for n, ke in enumerate(all_routers):
    #     print(f'{n}. {ke}')
    # print('==============')
    n = 0
    router_exclude_list = ['/health', '/openapi', '/users', '/parser', '/rawdatas']
    router_list = [route for route in get_all_routes
                   if not any((route.path.startswith(x) for x in router_exclude_list))]

    for m, ke in enumerate(router_list):
        try:
            _ = ke.openapi_extra.get('request_model') if hasattr(ke, 'openapi_extra') else None
            # ke.openapi_extra.get('request_model')
            # print(f'{m}. {ke}',
            #       ke.openapi_extra.get('request_model') if hasattr(ke, 'openapi_extra') else None)
        except Exception:
            n += 1
            print(f'{m}. {ke}', 'Nooo')
    print(f'{n} of {m}')


def test_routers(get_all_routes, get_get_routes, get_del_routes, get_post_routes, get_patch_routes):
    """
         выдает список рутов
    """
    all_in = len(get_all_routes)
    in_all = len(get_get_routes) + len(get_post_routes) + len(get_patch_routes) + len(get_del_routes)
    assert all_in == in_all
    n = 0
    router_exclude_list = ['/health', '/openapi', '/users', '/parser', '/rawdatas']
    router_list = [route for route in get_all_routes
                   if not any((route.path.startswith(x) for x in router_exclude_list))]
    for m, ke in enumerate(router_list):
        try:
            print(f"{m}. {ke} {ke.openapi_extra.get('request_model')}, {ke.response_model}")
        except Exception:
            n += 1
            print(f'{m}. {ke}', 'Nooo')
    print(f'{n} of {m}')


def test_post_routers(get_post_routes):
    n = 0
    method = 'POST'
    print(f'======{method=}')
    for m, ke in enumerate(get_post_routes):
        try:
            _ = ke.openapi_extra.get('request_model')
            print(f"{m}. {ke} {ke.openapi_extra.get('request_model')}")
        except Exception:
            n += 1
            print(f'{m}. {ke}', 'Nooo')
    print(f'всего роутеров {method}: {m} из них не имеют request_model: {n}')


def test_get_routers(get_get_routes):
    n = 0
    method = 'GET'
    print(f'======{method=}')
    for m, ke in enumerate(get_get_routes):
        try:
            _ = ke.openapi_extra.get('request_model')
            # print(f"{m}. {ke} {ke.openapi_extra.get('request_model')}")
        except Exception:
            n += 1
            print(f'{m}. {ke}', 'Nooo')
    print(f'всего роутеров {method}: {m} из них не имеют request_model: {n}')


def test_patch_routers(get_patch_routes):
    n = 0
    method = 'PATCH'
    print(f'======{method=}')
    for m, ke in enumerate(get_patch_routes):
        try:
            # _ = ke.openapi_extra.get('request_model')
            print(f"{m}. {ke} {ke.openapi_extra.get('request_model')}")
        except Exception:
            n += 1
            print(f'{m}. {ke}', 'Nooo')
    print(f'всего роутеров {method}: {m} из них не имеют request_model: {n}')


def test_delete_routers(get_del_routes):
    n = 0
    method = 'DELETE'
    print(f'======{method=}')
    for m, ke in enumerate(get_del_routes):
        try:
            _ = ke.openapi_extra.get('request_model')
            # print(f"{m}. {ke} {ke.openapi_extra.get('request_model')}")
        except Exception:
            n += 1
            print(f'{m}. {ke}', 'Nooo')
    print(f'всего роутеров {method}: {m} из них не имеют request_model: {n}')
