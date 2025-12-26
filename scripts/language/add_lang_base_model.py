#!/usr/bin/env python3
"""
Script to add language fields to base_model.py
"""
from pathlib import Path

def add_language_to_base_model(lang_codes: list):
    """Add language fields to BaseDescription and BaseLang classes in base_model.py"""
    base_model_file = Path('app/core/models/base_model.py')
    
    if not base_model_file.exists():
        print(f"Error: {base_model_file} does not exist")
        return False
    
    content = base_model_file.read_text()
    
    # Add description fields to BaseDescription class
    # Find the BaseDescription class and add the new fields
    base_desc_marker = "description_fr: Mapped[descr]"
    new_desc_fields = []
    for lang in lang_codes:
        new_desc_fields.append(f"    description_{lang}: Mapped[descr]")
    
    if base_desc_marker in content:
        # Insert new description fields after the french field
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip() == "description_fr: Mapped[descr]":
                for new_field in new_desc_fields:
                    new_lines.append(new_field)
    
        content = '\n'.join(new_lines)
    
    # Add name fields to BaseLang class
    base_lang_marker = "name_fr: Mapped[str_null_true]"
    new_name_fields = []
    for lang in lang_codes:
        # Special case: 'cn' should be 'zh' for Chinese in field names
        lang_code = 'zh' if lang == 'cn' else lang
        new_name_fields.append(f"    name_{lang_code}: Mapped[str_null_true]")
    
    if base_lang_marker in content:
        # Insert new name fields after the french field
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip() == "name_fr: Mapped[str_null_true]":
                for new_field in new_name_fields:
                    new_lines.append(new_field)
    
        content = '\n'.join(new_lines)
    
    # Update the __str__ method in BaseLang to include new languages
    str_method_marker = "return self.name or self.name_fr or self.name_ru or \"\""
    new_str_parts = []
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        new_str_parts.append(f"self.name_{lang_code}")
    
    if str_method_marker in content:
        # Replace the __str__ method to include new languages
        new_str_method = f"        return self.name or self.name_fr or self.name_ru or {' or '.join(new_str_parts)} or \"\""
        content = content.replace(str_method_marker, new_str_method)
    
    base_model_file.write_text(content)
    print(f"Added language fields to base_model.py for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Add Spanish and Chinese language codes
    add_language_to_base_model(['es', 'cn'])