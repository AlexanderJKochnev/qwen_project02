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


def test_get_localized_fields():
    from app.core.utils.translation_utils import get_localized_fields
    """ one time test for actual status (fields & langs on 01.01.2026)"""
    expected_result = ['name', 'name_fr', 'name_ru', 'description',
                       'description_fr', 'description_ru', 'title', 'title_fr',
                       'title_ru', 'subtitle', 'subtitle_fr', 'subtitle_ru']
    result = get_localized_fields()
    result.sort()
    expected_result.sort()
    assert result == expected_result
