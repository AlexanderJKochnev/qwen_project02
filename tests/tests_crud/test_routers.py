# tests/tests_crud/test_routers.py
"""
    compaire all routes and tested ones
"""
import pytest
# from app.core.utils.common_utils import jprint
# from tests.utility.assertion import assertions
pytestmark = pytest.mark.asyncio


def test_routers(simple_router_list, complex_router_list, routers_get_all, get_all_routes):
    all_routers = simple_router_list + complex_router_list
    for n, ke in enumerate(all_routers):
        print(f'{n}. {ke}')
    print('==============')
    for n, ke in enumerate(get_all_routes):
        if 'POST' in ke.methods:
            print(f'{n}. {ke}', ke.op)
