import pytest
from app.core.utils.alchemy_utils import JsonConverter
from app.core.utils.io_utils import get_filepath_from_dir_by_name
from app.core.utils.common_utils import jprint


@pytest.mark.skip
def test_jsonconverter():
    """ тестируем JsonConverter
        и структуру файлов
        data_2.json 149
        data.json   148
        data_old.json 139
    """
    from app.core.utils.json_validator import validate_json_file
    # error_list: list = []
    # image_list = await image_service.get_images_list_after_date()
    filepath = get_filepath_from_dir_by_name('data_2.json')
    # получаем список кортежей (image_name, image_id)
    # загружаем json файл, конвертируем в формат relation и собираем в список:
    expected_nmbr = validate_json_file(filepath)
    assert isinstance(expected_nmbr, int), expected_nmbr
    dataconv: list = list(JsonConverter(filepath)().values())
    assert len(dataconv) == expected_nmbr, f'{expected_nmbr=}, converted = {len(dataconv)}'


@pytest.mark.skip
def test_json_compaire():
    """ сравниваем файлы
        data_2.json 149
        data.json   148
        data_old.json 139
    """
    from app.core.utils.json_validator import validate_json_file
    files = ['data_2.json', 'data.json', 'data_old.json']
    dicts = []
    for item in files:
        filepath = get_filepath_from_dir_by_name(item)
        expected_nmbr = validate_json_file(filepath)
        assert isinstance(expected_nmbr, int), expected_nmbr
        dataconv: list = list(JsonConverter(filepath)().values())
        assert len(dataconv) == expected_nmbr, f'{expected_nmbr=}, converted = {len(dataconv)}'
        dicts.append(dataconv)
    for n, item in enumerate(dicts):
        if n < len(dicts) - 1:
            assert dicts[n] == dicts[n + 1]


@pytest.mark.skip
async def test_direct_import_data(authenticated_client_with_db, test_db_session):
    """
        тестирование загрузкит файлов из
    """
    from app.support.item.router import ItemRouter as Router
    client = authenticated_client_with_db
    router = Router()
    prefix = router.prefix
    # files = ['data_old.json', 'data_2.json', 'data.json']
    # for item in files:
    response = await client.post(f'{prefix}/direct')  # , content=item)
    assert response.status_code == 200, response.text

