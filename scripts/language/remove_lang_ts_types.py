#!/usr/bin/env python3
"""
Script to remove language fields from TypeScript base types
"""
from pathlib import Path

def remove_language_from_ts_types(lang_codes: list):
    """Remove language fields from LangFields interface in TypeScript base types"""
    ts_types_file = Path('preact_front/src/types/base.ts')
    
    if not ts_types_file.exists():
        print(f"Error: {ts_types_file} does not exist")
        return False
    
    content = ts_types_file.read_text()
    
    # Remove fields from the LangFields interface
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang
        name_field = f"  name_{lang_code}?: string;"
        desc_field = f"  description_{lang_code}?: string;"
        
        content = content.replace(name_field + '\n', '')
        content = content.replace(name_field, '')
        content = content.replace(desc_field + '\n', '')
        content = content.replace(desc_field, '')
    
    ts_types_file.write_text(content)
    print(f"Removed language fields from TypeScript types for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Remove Spanish and Chinese language codes
    remove_language_from_ts_types(['es', 'cn'])