#!/usr/bin/env python3
"""
Script to add language fields to drink model
"""
from pathlib import Path

def add_language_to_drink_model(lang_codes: list):
    """Add language fields to Lang class in drink model"""
    drink_model_file = Path('app/support/drink/model.py')
    
    if not drink_model_file.exists():
        print(f"Error: {drink_model_file} does not exist")
        return False
    
    content = drink_model_file.read_text()
    
    # Add fields to the Lang class for each field type
    field_types = ['title', 'subtitle', 'description', 'recommendation', 'madeof']
    
    for field_type in field_types:
        # Find the french field and add new ones after it
        fr_field_marker = f"{field_type}_fr: Mapped[descr]" if field_type in ['description', 'recommendation', 'madeof'] else f"{field_type}_fr: Mapped[str_null_true]"
        
        if fr_field_marker in content:
            new_fields = []
            for lang in lang_codes:
                lang_code = 'zh' if lang == 'cn' else lang
                field_type_annotation = "descr" if field_type in ['description', 'recommendation', 'madeof'] else "str_null_true"
                new_fields.append(f"    {field_type}_{lang_code}: Mapped[{field_type_annotation}]")
            
            # Insert new fields after the french field
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.strip() == fr_field_marker:
                    for new_field in new_fields:
                        new_lines.append(new_field)
            
            content = '\n'.join(new_lines)
    
    # Update the gin index to include the new language fields
    for field_type in field_types:
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            # Find the index creation part and add new fields
            index_marker = f"coalesce({field_type}_fr, '') || ' ' ||"
            new_index_part = f"             coalesce({field_type}_{lang_code}, '') || ' ' ||"
            
            content = content.replace(
                index_marker, 
                f"{index_marker}\n             {new_index_part}"
            )
    
    drink_model_file.write_text(content)
    print(f"Added language fields to drink model for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Add Spanish and Chinese language codes
    add_language_to_drink_model(['es', 'cn'])