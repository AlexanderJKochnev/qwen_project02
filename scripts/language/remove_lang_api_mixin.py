#!/usr/bin/env python3
"""
Script to remove language fields from API mixin
"""
from pathlib import Path

def remove_language_from_api_mixin(lang_codes: list):
    """Remove language fields from LangMixin class in API mixin"""
    api_mixin_file = Path('app/core/schemas/api_mixin.py')
    
    if not api_mixin_file.exists():
        print(f"Error: {api_mixin_file} does not exist")
        return False
    
    content = api_mixin_file.read_text()
    
    # Remove computed fields for each language
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        # Pattern to match the entire computed field block
        import re
        pattern = rf"(\s*)@computed_field\s*\n\s*@property\s*\n\s*def name_{lang_code}\(self\) -> str:\s*\n\s*return self\.__get_lang__\('_{lang_code}'\)\s*"
        content = re.sub(pattern, '', content)
    
    api_mixin_file.write_text(content)
    print(f"Removed language fields from API mixin for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Remove Spanish and Chinese language codes
    remove_language_from_api_mixin(['es', 'cn'])