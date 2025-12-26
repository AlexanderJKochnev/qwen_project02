#!/usr/bin/env python3
"""
Script to add language fields to TypeScript base types
"""
from pathlib import Path

def add_language_to_ts_types(lang_codes: list):
    """Add language fields to LangFields interface in TypeScript base types"""
    ts_types_file = Path('preact_front/src/types/base.ts')
    
    if not ts_types_file.exists():
        print(f"Error: {ts_types_file} does not exist")
        return False
    
    content = ts_types_file.read_text()
    
    # Add fields to the LangFields interface
    # Find the LangFields interface and add new fields
    lang_fields_marker = "  description_fr?: string;"
    
    if lang_fields_marker in content:
        new_fields = []
        for lang in lang_codes:
            # Special case: 'cn' should be 'zh' for Chinese in field names
            lang_code = 'zh' if lang == 'cn' else lang
            new_fields.append(f"  name_{lang_code}?: string;")
            new_fields.append(f"  description_{lang_code}?: string;")
        
        # Insert new fields after the french field
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip() == "  description_fr?: string;":
                for new_field in new_fields:
                    new_lines.append(f"  {new_field}")
        
        content = '\n'.join(new_lines)
    
    ts_types_file.write_text(content)
    print(f"Added language fields to TypeScript types for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Add Spanish and Chinese language codes
    add_language_to_ts_types(['es', 'cn'])