#!/usr/bin/env python3
"""
Script to dynamically update service methods to handle localized fields based on LANGS configuration.
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def update_item_service():
    """Update the item service to handle dynamic languages."""
    service_path = Path(__file__).parent.parent / "app" / "support" / "item" / "service.py"
    
    with open(service_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We need to update the transform_item_for_list_view method to handle dynamic languages
    # Instead of hardcoding 'en', 'ru', 'fr', we'll generate the code dynamically
    
    # First, let's extract the current transform_item_for_list_view method
    import re
    
    # Backup the original method
    backup_path = service_path.with_suffix('.py.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Find and replace the problematic parts in the transform_item_for_list_view method
    # We'll keep the existing method but modify it to be more flexible
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    
    # Generate dynamic code for the transform_item_for_list_view method
    # We'll replace the hardcoded language-specific code with a more dynamic approach
    updated_content = content
    
    # Replace the title localization section
    old_title_section = '''        # Локализация заголовка
        if lang == 'en':
            result['title'] = item['drink'].title
        elif lang == 'ru':
            title_ru = getattr(item['drink'], 'title_ru', None)
            if is_mock_object(title_ru):
                title_ru = None
            result['title'] = title_ru if title_ru else item['drink'].title
        elif lang == 'fr':
            title_fr = getattr(item['drink'], 'title_fr', None)
            if is_mock_object(title_fr):
                title_fr = None
            result['title'] = title_fr if title_fr else item['drink'].title
        else:
            result['title'] = item['drink'].title
'''
    
    # Generate new dynamic title localization code
    new_title_section = f'''        # Локализация заголовка - динамическая
        if lang == '{default_lang}':
            result['title'] = item['drink'].title
        else:
            # Check for the specific language version
            title_lang = getattr(item['drink'], f'title_{{lang}}', None)
            if is_mock_object(title_lang):
                title_lang = None
            result['title'] = title_lang if title_lang else item['drink'].title
'''
    
    # Replace the old section with the new one
    updated_content = updated_content.replace(old_title_section, new_title_section)
    
    # Replace the country localization section
    old_country_section = '''        # Локализация страны
        if lang == 'en':
            result['country'] = item['country'].name
        elif lang == 'ru':
            country_name_ru = getattr(item['country'], 'name_ru', None)
            if is_mock_object(country_name_ru):
                country_name_ru = None
            result['country'] = country_name_ru if country_name_ru else item['country'].name
        elif lang == 'fr':
            country_name_fr = getattr(item['country'], 'name_fr', None)
            if is_mock_object(country_name_fr):
                country_name_fr = None
            result['country'] = country_name_fr if country_name_fr else item['country'].name
        else:
            result['country'] = item['country'].name
'''
    
    # Generate new dynamic country localization code
    new_country_section = f'''        # Локализация страны - динамическая
        if lang == '{default_lang}':
            result['country'] = item['country'].name
        else:
            # Check for the specific language version
            country_name_lang = getattr(item['country'], f'name_{{lang}}', None)
            if is_mock_object(country_name_lang):
                country_name_lang = None
            result['country'] = country_name_lang if country_name_lang else item['country'].name
'''
    
    updated_content = updated_content.replace(old_country_section, new_country_section)
    
    # Replace the category localization section (this is more complex)
    # We need to replace the entire category localization block
    old_category_section = '''        # Локализация категории
        if lang == 'en':
            category_name = item['subcategory'].category.name
            subcategory_name = getattr(item['subcategory'], 'name', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if subcategory_name:
                result['category'] = f"{category_name} {subcategory_name}".strip()
            else:
                result['category'] = category_name
        elif lang == 'ru':
            category_name = getattr(item['subcategory'].category, 'name_ru', None)
            if is_mock_object(category_name):
                category_name = None
            if category_name:
                category_name = category_name
            else:
                category_name = item['subcategory'].category.name
            subcategory_name = getattr(item['subcategory'], 'name_ru', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if not subcategory_name:
                subcategory_name = getattr(item['subcategory'], 'name', None)
                if is_mock_object(subcategory_name):
                    subcategory_name = None
            if subcategory_name:
                result['category'] = f"{category_name} {subcategory_name}".strip()
            else:
                result['category'] = category_name
        elif lang == 'fr':
            category_name = getattr(item['subcategory'].category, 'name_fr', None)
            if is_mock_object(category_name):
                category_name = None
            if category_name:
                category_name = category_name
            else:
                category_name = item['subcategory'].category.name
            subcategory_name = getattr(item['subcategory'], 'name_fr', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if not subcategory_name:
                subcategory_name = getattr(item['subcategory'], 'name', None)
                if is_mock_object(subcategory_name):
                    subcategory_name = None
            if subcategory_name:
                result['category'] = f"{category_name} {subcategory_name}".strip()
            else:
                result['category'] = category_name
        else:
            category_name = item['subcategory'].category.name
            subcategory_name = getattr(item['subcategory'], 'name', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if subcategory_name:
                result['category'] = f"{category_name} {subcategory_name}".strip()
            else:
                result['category'] = category_name
'''
    
    new_category_section = f'''        # Локализация категории - динамическая
        if lang == '{default_lang}':
            category_name = item['subcategory'].category.name
            subcategory_name = getattr(item['subcategory'], 'name', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if subcategory_name:
                result['category'] = f"{{category_name}} {{subcategory_name}}".strip()
            else:
                result['category'] = category_name
        else:
            # Check for the specific language version
            category_name = getattr(item['subcategory'].category, f'name_{{lang}}', None)
            if is_mock_object(category_name):
                category_name = None
            if category_name:
                category_name = category_name
            else:
                category_name = item['subcategory'].category.name
            subcategory_name = getattr(item['subcategory'], f'name_{{lang}}', None)
            if is_mock_object(subcategory_name):
                subcategory_name = None
            if not subcategory_name:
                subcategory_name = getattr(item['subcategory'], 'name', None)
                if is_mock_object(subcategory_name):
                    subcategory_name = None
            if subcategory_name:
                result['category'] = f"{{category_name}} {{subcategory_name}}".strip()
            else:
                result['category'] = category_name
'''
    
    updated_content = updated_content.replace(old_category_section, new_category_section)
    
    # Write the updated content back to the file
    with open(service_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"Successfully updated item service to handle {len(langs)} languages dynamically")


def update_translation_utils():
    """Update translation utilities to handle dynamic languages."""
    translation_path = Path(__file__).parent.parent / "app" / "core" / "utils" / "translation_utils.py"
    
    with open(translation_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update the get_field_language function to handle dynamic language codes
    old_get_field_language = '''def get_field_language(field_name: str) -> Optional[str]:
    \"\"\"Extract language code from field name\"\"\"
    if field_name[-3] != '_':
        return 'en'
    return field_name[-2:]
'''
    
    # Generate new function that checks against available languages
    langs = settings.LANGUAGES
    langs_str = "', '".join(langs)
    
    new_get_field_language = f'''def get_field_language(field_name: str) -> Optional[str]:
    \"\"\"Extract language code from field name\"\"\"
    # Check if field ends with a known language suffix
    langs = settings.LANGUAGES
    for lang in langs:
        if field_name.endswith(f'_{{lang}}'):
            return lang
    # If no known language suffix found, assume default language
    return settings.DEFAULT_LANG
'''
    
    updated_content = content.replace(old_get_field_language, new_get_field_language)
    
    # Update the get_base_field_name function too
    old_get_base_field_name = '''def get_base_field_name(field_name: str) -> str:
    \"\"\"Get the base field name without language suffix
        DELETE !!!
    \"\"\"
    if field_name.endswith(('_ru', '_fr')):
        return field_name[:-3]  # Remove _ru or _fr
    return field_name
'''
    
    new_get_base_field_name = f'''def get_base_field_name(field_name: str) -> str:
    \"\"\"Get the base field name without language suffix
        DELETE !!!
    \"\"\"
    # Check against all configured languages
    langs = settings.LANGUAGES
    langs.sort(key=len, reverse=True)  # Sort by length descending to match longest first
    for lang in langs:
        if field_name.endswith(f'_{{lang}}'):
            return field_name[:-len(lang)-1]  # Remove _lang suffix
    return field_name
'''
    
    updated_content = updated_content.replace(old_get_base_field_name, new_get_base_field_name)
    
    # Write the updated content back to the file
    with open(translation_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print("Successfully updated translation utilities to handle dynamic languages")


def generate_pytest_for_dynamic_services():
    """Generate tests for the dynamic service generation functionality."""
    test_content = '''import pytest
from app.core.config.project_config import settings
from app.core.utils.translation_utils import get_field_language, get_base_field_name


def test_dynamic_translation_utils():
    """Test that translation utilities handle dynamic languages correctly."""
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    
    # Test get_field_language with various language codes
    for lang in langs:
        if lang != default_lang:
            field_name = f"title_{lang}"
            detected_lang = get_field_language(field_name)
            assert detected_lang == lang, f"Expected {lang}, got {detected_lang} for field {field_name}"
    
    # Test get_field_language with default language (should return default)
    field_name = "title"
    detected_lang = get_field_language(field_name)
    assert detected_lang == default_lang, f"Expected {default_lang}, got {detected_lang} for field {field_name}"


def test_get_base_field_name():
    """Test that get_base_field_name works with dynamic languages."""
    langs = settings.LANGUAGES
    
    # Test with various language suffixed fields
    for lang in langs:
        if lang != settings.DEFAULT_LANG:
            suffixed_field = f"description_{lang}"
            base_field = get_base_field_name(suffixed_field)
            assert base_field == "description", f"Expected 'description', got '{base_field}' for '{suffixed_field}'"
    
    # Test with non-suffixed field
    base_field = get_base_field_name("title")
    assert base_field == "title", f"Expected 'title', got '{base_field}'"
'''
    
    # Write test file
    test_path = Path(__file__).parent.parent / "tests" / "tests_common" / "test_dynamic_services.py"
    os.makedirs(test_path.parent, exist_ok=True)
    
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("Generated test file for dynamic services")


if __name__ == "__main__":
    update_item_service()
    update_translation_utils()
    generate_pytest_for_dynamic_services()
    print("Dynamic service generation completed!")