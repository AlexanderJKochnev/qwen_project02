#!/usr/bin/env python3
"""
Script to remove language fields from base schemas
"""
from pathlib import Path

def remove_language_from_base_schemas(lang_codes: list):
    """Remove language fields from base schema classes"""
    base_schema_file = Path('app/core/schemas/base.py')
    
    if not base_schema_file.exists():
        print(f"Error: {base_schema_file} does not exist")
        return False
    
    content = base_schema_file.read_text()
    
    # Remove fields from DescriptionSchema class
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        desc_field = f"    description_{lang_code}: Optional[str] = None"
        content = content.replace(desc_field + '\n', '')
        content = content.replace(desc_field, '')
    
    # Remove fields from DescriptionExcludeSchema class
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        desc_exclude_field = f"    description_{lang_code}: Optional[str] = Field(exclude=True)"
        content = content.replace(desc_exclude_field + '\n', '')
        content = content.replace(desc_exclude_field, '')
    
    # Remove fields from NameSchema class
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        name_field = f"    name_{lang_code}: Optional[str] = None"
        content = content.replace(name_field + '\n', '')
        content = content.replace(name_field, '')
    
    # Remove fields from NameExcludeSchema class
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        name_exclude_field = f"    name_{lang_code}: Optional[str] = Field(exclude=True)"
        content = content.replace(name_exclude_field + '\n', '')
        content = content.replace(name_exclude_field, '')
    
    base_schema_file.write_text(content)
    print(f"Removed language fields from base schemas for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Remove Spanish and Chinese language codes
    remove_language_from_base_schemas(['es', 'cn'])