#!/usr/bin/env python3
"""
Script to remove language fields from base_model.py
"""
from pathlib import Path

def remove_language_from_base_model(lang_codes: list):
    """Remove language fields from BaseDescription and BaseLang classes in base_model.py"""
    base_model_file = Path('app/core/models/base_model.py')
    
    if not base_model_file.exists():
        print(f"Error: {base_model_file} does not exist")
        return False
    
    content = base_model_file.read_text()
    
    # Remove description fields
    for lang in lang_codes:
        description_field = f"    description_{lang}: Mapped[descr]"
        content = content.replace(description_field + '\n', '')
        content = content.replace(description_field, '')
    
    # Remove name fields (using correct language codes)
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        name_field = f"    name_{lang_code}: Mapped[str_null_true]"
        content = content.replace(name_field + '\n', '')
        content = content.replace(name_field, '')
    
    # Update the __str__ method to remove references to new languages
    # Remove the new language references from the __str__ method
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        lang_ref = f" or self.name_{lang_code}"
        content = content.replace(lang_ref, '')
    
    base_model_file.write_text(content)
    print(f"Removed language fields from base_model.py for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Remove Spanish and Chinese language codes
    remove_language_from_base_model(['es', 'cn'])