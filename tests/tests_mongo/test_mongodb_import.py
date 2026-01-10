# tests/test_mongodb_import.py
"""
    тестирование импорта
"""

from pathlib import Path

import pytest

# from app.mongodb.config import mongodb
from app.core.config.project_config import get_path_to_root, settings
from app.core.utils.common_utils import jprint

pytestmark = pytest.mark.asyncio


async def test_import():  # authenticated_client_with_db, test_db_session):
    """ тестирует импорт """
    from app.core.utils.alchemy_utils import JsonConverter
    from collections import Counter
    filename = settings.JSON_FILENAME
    upload_dir = settings.UPLOAD_DIR
    dirpath: Path = get_path_to_root(upload_dir)
    filepath = dirpath / filename
    dataconv: list = list(JsonConverter(filepath)().values())
    len1 = len(dataconv)
    images = list({a['image_path'] for a in dataconv})
    len2 = len(images)
    titles = [a['title'] for a in dataconv]
    element_counts = Counter(titles)
    duplicates = [item for item, count in element_counts.items() if count > 1]
    len3 = len(titles)
    jprint(element_counts)
    assert len1 == len2, f'{len1} {len2}'
    assert not duplicates, duplicates
