# tests/tests_new/test_routes.py
"""
    проверка методов post c валидацией входящих и исходящих данных
    эта группа тестов падает если запускать их вместе с другими тесатми - очередность не важна
    разобраться
"""

import pytest
from app.core.utils.common_utils import jprint
from tests.utility.assertion import assertions
pytestmark = pytest.mark.asyncio