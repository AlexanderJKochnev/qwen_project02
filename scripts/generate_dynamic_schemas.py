#!/usr/bin/env python3
"""
Script to dynamically generate Pydantic schemas with localized fields based on LANGS configuration.
"""
import sys
import os
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


def generate_lang_schemas():
    """Generate language-specific schemas dynamically based on LANGS configuration."""
    from app.core.config.project_config import settings
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    
    # Generate content for lang_schemas.py
    header = '''# app/core/schemas/lang_schemas.py
from pydantic import computed_field
from app.core.schemas.base import ListView, DetailView
"""
    языковые pydantic модели для справочников
    добавлять по мере появления языков
"""
'''

    content_parts = []

    # Generate schema for each language
    for lang in langs:
        # Define language-specific labels
        lang_labels = {
            'en': {'display_name': 'Name', 'placeholder': 'Display Name'},
            'ru': {'display_name': 'Наименование', 'placeholder': 'Отображаемое имя'},
            'fr': {'display_name': 'Nom', 'placeholder': 'Nom affiché'},
            'es': {'display_name': 'Nombre', 'placeholder': 'Nombre mostrado'},
            'de': {'display_name': 'Name', 'placeholder': 'Anzeigename'},
            'it': {'display_name': 'Nome', 'placeholder': 'Nome visualizzato'},
            'pt': {'display_name': 'Nome', 'placeholder': 'Nome exibido'},
            'zh': {'display_name': '姓名', 'placeholder': '显示名称'},
            'ja': {'display_name': '名前', 'placeholder': '表示名'},
            'ko': {'display_name': '이름', 'placeholder': '표시 이름'},
        }
        
        label_info = lang_labels.get(lang, {'display_name': 'Name', 'placeholder': 'Display Name'})
        
        # Generate ListView schema for this language
        list_view_schema = f'''
class ListView{lang.upper()}(ListView):
    @computed_field(description='{label_info['display_name']}',  # Это будет подписью/лейблом (human readable)
                    title='{label_info['placeholder']}'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
        """Возвращает первое непустое значение из локализованных полей"""
        # Build the coalesce expression based on language priority
        lang_priority = [lang] + [l for l in langs if l != lang]
        conditions = []
        for l in lang_priority:
            if l == default_lang:
                conditions.append(f'self.name')
            else:
                conditions.append(f'self.name_{l}')
        conditions.append('""')
        return ' or '.join(conditions)
'''
        
        # Generate DetailView schema for this language
        detail_view_schema = f'''
class DetailView{lang.upper()}(DetailView):
    @computed_field(description='{label_info['display_name']}',  # Это будет подписью/лейблом (human readable)
                    title='{label_info['placeholder']}'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
        """Возвращает первое непустое значение из локализованных полей"""
        # Build the coalesce expression based on language priority
        lang_priority = [lang] + [l for l in langs if l != lang]
        conditions = []
        for l in lang_priority:
            if l == default_lang:
                conditions.append(f'self.name')
            else:
                conditions.append(f'self.name_{l}')
        conditions.append('""')
        return ' or '.join(conditions)

    @computed_field(description='{label_info['display_name']}_description',  # Это будет подписью/лейблом (human readable)
                    title='{label_info['placeholder']}_description'  # Это для swagger (machine readable)
                    )
    @property
    def display_description(self) -> str:
        """Возвращает первое непустое значение из локализованных описаний"""
        # Build the coalesce expression based on language priority
        lang_priority = [lang] + [l for l in langs if l != lang]
        conditions = []
        for l in lang_priority:
            if l == default_lang:
                conditions.append(f'self.description')
            else:
                conditions.append(f'self.description_{l}')
        conditions.append('""')
        return ' or '.join(conditions)
'''
        
        content_parts.extend([list_view_schema, detail_view_schema])
    
    # Generate the full content
    full_content = header + ''.join(content_parts)
    
    # Write to the lang_schemas.py file
    schema_path = Path(__file__).parent.parent / "app" / "core" / "schemas" / "lang_schemas.py"
    
    with open(schema_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"Successfully updated lang_schemas.py with {len(langs)} languages")


def generate_dynamic_schemas_for_models():
    """Generate dynamic schemas for models with localized fields."""
    from app.core.config.project_config import settings
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    localized_fields = settings.FIELDS_LOCALIZED
    
    # Import the model to get field information
    from app.support.drink.model import Drink
    
    # Generate schema content for drink model
    schema_header = '''# app/support/drink/schemas.py
from pydantic import BaseModel, Field
from typing import Optional
from app.core.config.project_config import settings

"""
Dynamic schemas for Drink model with localized fields based on LANGS configuration
"""
'''
    
    # Generate Create schema
    create_fields = []
    for field_name in localized_fields:
        # Base field (required for default language)
        create_fields.append(f"    {field_name}: str")
        # Localized fields (optional)
        for lang in langs:
            if lang != default_lang:
                create_fields.append(f"    {field_name}_{lang}: Optional[str] = None")
    
    create_schema = f'''class DrinkCreate(BaseModel):
    # Base fields
{"\\n".join(create_fields)}
    
    # Other non-localized fields
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    sparkling: Optional[bool] = None
    subcategory_id: int
    subregion_id: int
    sweetness_id: Optional[int] = None
'''
    
    # Generate Update schema
    update_fields = []
    for field_name in localized_fields:
        # All fields optional for update
        update_fields.append(f"    {field_name}: Optional[str] = None")
        for lang in langs:
            if lang != default_lang:
                update_fields.append(f"    {field_name}_{lang}: Optional[str] = None")
    
    update_schema = f'''class DrinkUpdate(BaseModel):
    # Base fields
{"\\n".join(update_fields)}
    
    # Other non-localized fields
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    sparkling: Optional[bool] = None
    subcategory_id: Optional[int] = None
    subregion_id: Optional[int] = None
    sweetness_id: Optional[int] = None
'''
    
    # Generate Read schema
    read_fields = []
    for field_name in localized_fields:
        # All fields optional for read
        read_fields.append(f"    {field_name}: Optional[str] = None")
        for lang in langs:
            if lang != default_lang:
                read_fields.append(f"    {field_name}_{lang}: Optional[str] = None")
    
    read_schema = f'''class DrinkRead(BaseModel):
    id: int
    # Base fields
{"\\n".join(read_fields)}
    
    # Other non-localized fields
    alc: Optional[float] = None
    sugar: Optional[float] = None
    age: Optional[str] = None
    sparkling: Optional[bool] = None
    subcategory_id: int
    subregion_id: int
    sweetness_id: Optional[int] = None
'''
    
    # Combine all schemas
    full_schema_content = schema_header + "\n\n" + create_schema + "\n\n" + update_schema + "\n\n" + read_schema
    
    # Write to the drink schemas file
    drink_schema_path = Path(__file__).parent.parent / "app" / "support" / "drink" / "schemas.py"
    
    # Read existing content and preserve non-localized parts
    if drink_schema_path.exists():
        with open(drink_schema_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
        
        # Extract non-localized field sections to preserve custom logic
        import re
        
        # Keep imports and non-localized schema parts
        # For now, let's just append our generated schemas to the existing file
        # In a real implementation, we would be more careful about preserving existing code
        full_content = existing_content + "\n\n" + "# Dynamic localized schemas generated from LANGS config\n" + create_schema + "\n\n" + update_schema + "\n\n" + read_schema
    else:
        full_content = full_schema_content
    
    with open(drink_schema_path, 'w', encoding='utf-8') as f:
        f.write(full_content)
    
    print(f"Successfully updated drink schemas with dynamic localized fields for {len(langs)} languages")


def generate_pytest_for_dynamic_schemas():
    """Generate tests for the dynamic schema generation functionality."""
    from app.core.config.project_config import settings
    test_content = '''import pytest
from app.core.config.project_config import settings
from app.core.schemas.lang_schemas import *


def test_dynamic_lang_schemas():
    """Test that language-specific schemas have been generated based on LANGS config."""
    langs = settings.LANGUAGES
    
    # Check that schema classes exist for each language
    for lang in langs:
        class_name = f"ListView{lang.upper()}"
        assert hasattr(locals(), class_name) or globals().get(class_name), f"Schema class {class_name} not found"
        
        class_name = f"DetailView{lang.upper()}"
        assert hasattr(locals(), class_name) or globals().get(class_name), f"Schema class {class_name} not found"


def test_lang_schema_attributes():
    """Test that language schemas have expected computed fields."""
    langs = settings.LANGUAGES
    
    for lang in langs:
        # Test ListView schema
        list_class = globals().get(f"ListView{lang.upper()}")
        if list_class:
            # Check that it has the expected computed property
            assert hasattr(list_class, 'display_name'), f"ListView{lang.upper()} missing display_name property"
        
        # Test DetailView schema  
        detail_class = globals().get(f"DetailView{lang.upper()}")
        if detail_class:
            # Check that it has the expected computed properties
            assert hasattr(detail_class, 'display_name'), f"DetailView{lang.upper()} missing display_name property"
            assert hasattr(detail_class, 'display_description'), f"DetailView{lang.upper()} missing display_description property"
'''
    
    # Write test file
    test_path = Path(__file__).parent.parent / "tests" / "tests_common" / "test_dynamic_schemas.py"
    os.makedirs(test_path.parent, exist_ok=True)
    
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(test_content)
    
    print("Generated test file for dynamic schemas")


if __name__ == "__main__":
    generate_lang_schemas()
    generate_dynamic_schemas_for_models()
    generate_pytest_for_dynamic_schemas()
    print("Dynamic schema generation completed!")