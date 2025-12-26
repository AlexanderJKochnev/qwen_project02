#!/usr/bin/env python3
"""
Script to add language fields to API mixin
"""
from pathlib import Path

def add_language_to_api_mixin(lang_codes: list):
    """Add language fields to LangMixin class in API mixin"""
    api_mixin_file = Path('app/core/schemas/api_mixin.py')
    
    if not api_mixin_file.exists():
        print(f"Error: {api_mixin_file} does not exist")
        return False
    
    content = api_mixin_file.read_text()
    
    # Add computed fields for each language
    # Find the last computed field and add new ones after it
    last_computed_field_marker = "def name_fr(self) -> str:"
    
    if last_computed_field_marker in content:
        new_fields = []
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            new_fields.append(f"""
    @computed_field
    @property
    def name_{lang_code}(self) -> str:
        return self.__get_lang__('_{lang_code}')""")
        
        # Insert new fields after the french field
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if 'def name_fr(self) -> str:' in line:
                # Find the end of the name_fr method and add new fields after it
                for new_field in new_fields:
                    new_lines.extend(new_field.split('\n'))
    
        content = '\n'.join(new_lines)
    
    api_mixin_file.write_text(content)
    print(f"Added language fields to API mixin for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Add Spanish and Chinese language codes
    add_language_to_api_mixin(['es', 'cn'])