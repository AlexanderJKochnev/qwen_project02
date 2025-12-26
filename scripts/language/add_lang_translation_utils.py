#!/usr/bin/env python3
"""
Script to add language fields to translation utilities
"""
from pathlib import Path

def add_language_to_translation_utils(lang_codes: list):
    """Add language fields to translation utilities"""
    trans_utils_file = Path('app/core/utils/translation_utils.py')
    
    if not trans_utils_file.exists():
        print(f"Error: {trans_utils_file} does not exist")
        return False
    
    content = trans_utils_file.read_text()
    
    # Update get_localized_fields function to include new languages
    localized_fields_marker = "'title', 'title_fr', 'title_ru',"
    new_localized_fields = []
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        new_localized_fields.extend([
            f"        'name_{lang_code}',",
            f"        'description_{lang_code}',",
            f"        'title_{lang_code}',",
            f"        'subtitle_{lang_code}',"
        ])
    
    if localized_fields_marker in content:
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if "'title', 'title_fr', 'title_ru'," in line:
                for new_field in new_localized_fields:
                    new_lines.append(new_field)
        
        content = '\n'.join(new_lines)
    
    # Update get_field_language function to recognize new languages
    # Replace the function with updated version
    old_get_field_language = '''def get_field_language(field_name: str) -> Optional[str]:
    """Extract language code from field name"""
    if field_name.endswith('_ru'):
        return 'ru'
    elif field_name.endswith('_fr'):
        return 'fr'
    elif field_name in ['name', 'description', 'title', 'subtitle']:
        return 'en'  # Assuming English is the base language
    return None'''
    
    new_get_field_language = '''def get_field_language(field_name: str) -> Optional[str]:
    """Extract language code from field name"""
    if field_name.endswith('_ru'):
        return 'ru'
    elif field_name.endswith('_fr'):
        return 'fr'''
    
    # Add new languages to the function
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        new_get_field_language += f'''
    elif field_name.endswith('_{lang_code}'):
        return '{lang_code}' '''
    
    new_get_field_language += '''
    elif field_name in ['name', 'description', 'title', 'subtitle']:
        return 'en'  # Assuming English is the base language
    return None'''
    
    content = content.replace(old_get_field_language, new_get_field_language)
    
    # Update get_base_field_name function to handle new languages
    old_get_base_field_name = '''def get_base_field_name(field_name: str) -> str:
    """Get the base field name without language suffix"""
    if field_name.endswith(('_ru', '_fr')):
        return field_name[:-3]  # Remove _ru or _fr
    return field_name'''
    
    new_get_base_field_name = '''def get_base_field_name(field_name: str) -> str:
    """Get the base field name without language suffix"""
    if field_name.endswith(('_ru', '_fr'''
    
    # Add new language suffixes
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        new_get_base_field_name += f", '_{lang_code}'"
    
    new_get_base_field_name += ''')):
        suffix_len = max(len('_ru'), len('_fr')'''
    
    # Calculate max suffix length for new languages
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        new_get_base_field_name += f", len('_{lang_code}')"
    
    new_get_base_field_name += ''')
        return field_name[:-suffix_len]  # Remove language suffix
    return field_name'''
    
    content = content.replace(old_get_base_field_name, new_get_base_field_name)
    
    trans_utils_file.write_text(content)
    print(f"Added language support to translation utilities for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Add Spanish and Chinese language codes
    add_language_to_translation_utils(['es', 'cn'])