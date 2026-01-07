# tests/tests_common/test_translation_utils.py
import pytest
from app.core.config.project_config import settings

pytestmark = pytest.mark.asyncio

source: dict = {'name': 'english name',
                'name_ru': None,
                'name_fr': 'french_name',
                'title': None,
                'title_ru': 'russian title',
                'title_fr': None,
                'subtitle': None,
                'subtitle_ru': None,
                'subtityle_fr': None}


async def test_fill_missing_translations():
    from app.core.utils.translation_utils import fill_missing_translations
    ai = settings.MACHINE_TRANSLATION_MARK
    expected_result: dict = {'name': 'english name',
                             'name_ru': f"english name <{ai}>",
                             'name_fr': 'french_name',
                             'title': f"russian title <{ai}>",
                             'title_ru': 'russian title',
                             'title_fr': f"russian title <{ai}>",
                             'subtitle': None,
                             'subtitle_ru': None,
                             'subtityle_fr': None}
    result = await fill_missing_translations(source, test=True)
    assert result == expected_result
