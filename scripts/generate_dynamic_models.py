#!/usr/bin/env python3
"""
Script to dynamically generate SQLAlchemy model classes with localized fields based on LANGS configuration.
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_lang_mixin():
    """Generate Lang mixin class with dynamic localized fields based on LANGS."""
    from app.core.config.project_config import settings
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    
    # Generate field definitions for each localized field
    localized_fields = settings.FIELDS_LOCALIZED
    field_definitions = []
    
    for field_name in localized_fields:
        # Add the default field (no suffix for default language)
        field_definitions.append(f"    {field_name}: Mapped[str_null_false]")
        
        # Add localized fields for each language except the default
        for lang in langs:
            if lang != default_lang:
                field_definitions.append(f"    {field_name}_{lang}: Mapped[str_null_true]")
    
    # Generate the complete Lang class
    lang_class = [
        "class Lang:",
        "    __abstract__ = True",
    ]
    
    lang_class.extend(field_definitions)
    lang_class.append("")  # Empty line at the end
    
    return "\n".join(lang_class)


def generate_gin_index_sql():
    """Generate GIN index SQL with dynamic localized fields based on LANGS."""
    from app.core.config.project_config import settings
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    
    localized_fields = settings.FIELDS_LOCALIZED
    
    # Build the coalesce expression for GIN index
    index_parts = []
    for field_name in localized_fields:
        # Add the default field first
        index_parts.append(f"            coalesce({field_name}, '')")
        
        # Add localized fields for each language except the default
        for lang in langs:
            if lang != default_lang:
                index_parts.append(f"            coalesce({field_name}_{lang}, '')")
    
    # Join all parts with ' || ' for concatenation
    index_expr = " || ' ' ||\n".join(index_parts)
    
    gin_index_sql = f'''
create_gin_index_sql = DDL("""
    CREATE INDEX drink_trigram_idx_combined ON drinks
        USING gin (
            ({index_expr})
            gin_trgm_ops
        );
    """)
'''
    
    return gin_index_sql


def update_drink_model():
    """Update the drink model with dynamically generated Lang mixin and GIN index."""
    from app.core.config.project_config import settings
    
    # Read the original model file
    model_path = Path(__file__).parent.parent / "app" / "support" / "drink" / "model.py"
    
    with open(model_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Generate new Lang class
    new_lang_class = generate_lang_mixin()
    
    # Replace the existing Lang class
    import re
    
    # Find and replace the Lang class
    lang_class_pattern = r'class Lang:.*?(?=^\s*class|\Z)'
    content = re.sub(
        r'class Lang:.*?(?=\n\s*class|\n\s*create_gin_index_sql|\Z)', 
        new_lang_class.rstrip(), 
        content, 
        flags=re.DOTALL | re.MULTILINE
    )
    
    # Generate and replace the GIN index
    new_gin_index = generate_gin_index_sql()
    
    # Replace the existing GIN index
    gin_pattern = r'create_gin_index_sql = DDL\(.*?"GIN_INDEX_PLACEHOLDER"\).*?\n.*?event\.listen\(.*?\n'
    if 'create_gin_index_sql' in content:
        # More specific pattern for the GIN index section
        gin_section_pattern = r'create_gin_index_sql = DDL\(.*?\);[\s\S]*?event\.listen\(\s*Drink\.__table__,\s*\'after_create\',\s*create_gin_index_sql\s*\)'
        content = re.sub(gin_section_pattern, new_gin_index.strip() + '\n\n# Привязываем этот DDL к событию создания таблицы Drink\n# Это гарантирует, что индекс будет создан сразу после создания таблицы\n# если индекс добавлен после создания таблицы - запустить create_trigram.sh\nevent.listen(\n    Drink.__table__,\n    \'after_create\',\n    create_gin_index_sql\n)', content, flags=re.DOTALL)
    else:
        # If no existing GIN index, append the new one before the end of the file
        content = content.rstrip() + "\n\n" + new_gin_index.strip() + '\n\n# Привязываем этот DDL к событию создания таблицы Drink\n# Это гарантирует, что индекс будет создан сразу после создания таблицы\n# если индекс добавлен после создания таблицы - запустить create_trigram.sh\nevent.listen(\n    Drink.__table__,\n    \'after_create\',\n    create_gin_index_sql\n)\n'
    
    # Write the updated content back to the file
    with open(model_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Successfully updated drink model with dynamic localized fields")


def generate_pytest_for_dynamic_models():
    """Generate tests for the dynamic model generation functionality."""
    test_content = '''import pytest
from app.support.drink.model import Lang
from app.core.config.project_config import settings


def test_dynamic_lang_fields():
    """Test that Lang class has the expected localized fields based on LANGS config."""
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    localized_fields = settings.FIELDS_LOCALIZED
    
    # Check that Lang class has all expected fields
    lang_attrs = [attr for attr in dir(Lang) if not attr.startswith('_')]
    
    for field in localized_fields:
        # Default field should exist without suffix
        assert field in lang_attrs, f"Field '{field}' missing from Lang class"
        
        # Localized fields should exist for each language except default
        for lang in langs:
            if lang != default_lang:
                localized_field = f"{field}_{lang}"
                assert localized_field in lang_attrs, f"Localized field '{localized_field}' missing from Lang class"


def test_lang_mixin_generation():
    """Test that the Lang mixin is properly structured."""
    # Verify that Lang is an abstract class
    assert getattr(Lang, '__abstract__', False) == True, "Lang class should be abstract"
    
    # Verify that the class has expected attributes
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    localized_fields = settings.FIELDS_LOCALIZED
    
    # Count expected fields
    expected_count = len(localized_fields)  # base fields
    for lang in langs:
        if lang != default_lang:
            expected_count += len(localized_fields)  # localized fields per additional language
    
    # Get actual attributes that look like field definitions
    actual_fields = [attr for attr in dir(Lang) if not attr.startswith('_') and not callable(getattr(Lang, attr))]
    
    # At least the expected fields should be present
    assert len(actual_fields) >= expected_count, f"Expected at least {expected_count} fields, got {len(actual_fields)}"
'''
    
    # Write test file
    test_path = Path(__file__).parent.parent / "tests" / "tests_common" / "test_dynamic_models.py"
    os.makedirs(test_path.parent, exist_ok=True)
    
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("Generated test file for dynamic models")


if __name__ == "__main__":
    update_drink_model()
    generate_pytest_for_dynamic_models()
    print("Dynamic model generation completed!")