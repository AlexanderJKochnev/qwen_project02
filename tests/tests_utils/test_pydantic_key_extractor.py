# tests/tests_utils/test_pydantic_key_extractor.py
from app.core.utils.common_utils import jprint
from app.core.utils.pydantic_key_extractor import extract_keys_with_blacklist


def test_extract_keys_with_blacklist():
    """
    тестирование утилиты extract_keys_with_blacklist
    создание списка ключей точечной нотации для Pydatnic модели
    """
    from app.support.item.schemas import ItemReadRelation
    blacklist = ['vol', 'alc', 'price', 'id', 'updated_at', 'created_at', 'count']
    result = extract_keys_with_blacklist(ItemReadRelation, blacklist)
    jprint(result)
