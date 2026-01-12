# tests/test_patch.py
"""
    тестируем все методы UPDATE ()
    новые методы добавляются автоматически
    pytest tests/test_patch.py --tb=auto --disable-warnings -vv --capture=no
"""
import pytest
from app.core.utils.common_utils import jprint
from tests.data_factory.fake_generator import generate_test_data
from tests.conftest import get_model_by_name

pytestmark = pytest.mark.asyncio


async def test_patch_routers(authenticated_client_with_db, get_patch_routes):
    source = get_patch_routes
    client = authenticated_client_with_db
    result: dict = {}
    fault_nmbr = 0
    good_nmbr = 0
    for n, route in enumerate(source):
        try:
            path = route.path
            request_model_name = route.openapi_extra.get('x-request-schema')
            request_model = get_model_by_name(request_model_name)
            id = 3    # модифицируем 3 запись
            path = route.path.replace('{id}', f'{id}')
            test_data = generate_test_data(
                request_model, 2,
                {'int_range': (1, 2), 'decimal_range': (0.5, 1), 'float_range': (0.1, 1.0),
                 # 'field_overrides': {'name': 'Special Product'},
                 'faker_seed': 42}
            )
            if not test_data:
                fault_nmbr += 1
                result[path] = 'test_data was not generated'
                continue
            data = next(test_data, None)
            response = await client.get(f"{path}/{id}")
            sts = response.status_code
            response = await client.patch(f"{path}/{id}", json=data)
            print(f"{sts=}", f"{response.status_code=}  {path=}", )
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
async def test_patch_success(authenticated_client_with_db, test_db_session,
                             simple_router_list, complex_router_list, fakedata_generator):
    """
        тестирует методы PATCH (patch) - c проверкой id
        доделать
    """
    client = authenticated_client_with_db
    routers = simple_router_list + complex_router_list
    test_data: dict = {'name': 'updated_name', 'description': 'updated description',
                       'name_ru': 'обновленные данные', 'description_ru': 'обновленные данные'
                       }
    drink_data: dict = {'description': 'updated description', 'title': 'updated_title',
                        'description_ru': 'обновленные данные',
                        'title_ru': 'обновленные данные title'}
    item_data: dict = {'vol': 1.0,
                       # 'price': 1.0,   # this field is muted in read_relation schema
                       'image_id': 'image_pathe updated'}
    customer_data: dict = {'login': 'test_data',
                           'firstname': 'test_data'}
    item_id = 1
    for router_class in routers:
        router = router_class()
        prefix = router.prefix
        # read_schema_relations = router.read_schema_relation
        if prefix == '/drinks':
            source = drink_data
        elif prefix == '/items':
            source = item_data
        elif prefix == '/customers':
            source = customer_data
        else:
            source = test_data
        response = await client.patch(f"{prefix}/{item_id}", json=source)
        # Assert
        if response.status_code != 200:
            print(f'====={prefix}====={item_id}===')
            jprint(source)
        assert response.status_code == 200, response.text
        response_data = response.json()
        assert response_data["id"] == item_id
        for key, val in source.items():
            if response_data.get(key) != val:
                jprint(response_data)
            assert response_data.get(key) == val, f'{prefix=}, {key=}, {val=} {response_data.get(key)=}'


@pytest.mark.skip
async def test_patch_success2(authenticated_client_with_db, test_db_session,
                              simple_router_list, complex_router_list, fakedata_generator):
    """
        тестирует методы PATCH (patch) - c проверкой id
    """
    client = authenticated_client_with_db
    routers = simple_router_list + complex_router_list
    for router_class in routers:
        router = router_class()
        prefix = router.prefix
        if prefix in ['/api', '/items', '/images']:  # api не имеет метода all, удалить когда заведется
            continue
        response = await client.get(f'{prefix}/all')
        if response.status_code != 200:
            print(response.text)
        assert response.status_code == 200, f'{prefix=}, {response.text}'
        interim_result = response.json()
        assert isinstance(interim_result, list), f'{prefix=}, неверный результат метода get_all'
        origin_dict = interim_result[-1]
        id = origin_dict.pop('id', None)
        if id is None:
            jprint(origin_dict)
        assert id is not None, f'{prefix=}, неверный результат метода get_all - отсутвует id'
        updated_dict = {key: f'updated {val}' for key, val in origin_dict.items()
                        if isinstance(val, str) and not val.endswith('%')}
        response = await client.patch(f"{prefix}/{id}", json=updated_dict)
        if response.status_code != 200:
            print(response.text)
        assert response.status_code == 200, f'{prefix=} ошибка обновления'
