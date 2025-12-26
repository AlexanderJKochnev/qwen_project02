#!/usr/bin/env python3
"""
Script to remove language fields from drink model
"""
from pathlib import Path

def remove_language_from_drink_model(lang_codes: list):
    """Remove language fields from Lang class in drink model"""
    drink_model_file = Path('app/support/drink/model.py')
    
    if not drink_model_file.exists():
        print(f"Error: {drink_model_file} does not exist")
        return False
    
    content = drink_model_file.read_text()
    
    # Remove fields from the Lang class for each field type
    field_types = ['title', 'subtitle', 'description', 'recommendation', 'madeof']
    
    for field_type in field_types:
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            field_type_annotation = "descr" if field_type in ['description', 'recommendation', 'madeof'] else "str_null_true"
            field_line = f"    {field_type}_{lang_code}: Mapped[{field_type_annotation}]"
            content = content.replace(field_line + '\n', '')
            content = content.replace(field_line, '')
    
    # Remove the gin index entries for the new languages
    for field_type in field_types:
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            index_part = f"             coalesce({field_type}_{lang_code}, '') || ' ' ||"
            content = content.replace(index_part + '\n', '')
            content = content.replace(index_part, '')
    
    drink_model_file.write_text(content)
    print(f"Removed language fields from drink model for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Remove Spanish and Chinese language codes
    remove_language_from_drink_model(['es', 'cn'])