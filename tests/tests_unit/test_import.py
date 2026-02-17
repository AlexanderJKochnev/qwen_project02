# tests/test_imports.py
def test_no_circular_imports():
    """Тест на отсутствие циклических импортов"""
    import sys

    # Попробуйте импортировать модули в порядке, который раньше вызывал ошибки
    from app.core.repositories.sqlalchemy_repository import Repository
    from app.core.services.service import Service
    from app.core.utils.translation_utils import translate_text
    from app.support.category.service import CategoryService

    assert True  # Если дошли сюда - циклических импортов нет
