#!/usr/bin/env python3
"""
Script to add language fields to base schemas
"""
from pathlib import Path

def add_language_to_base_schemas(lang_codes: list):
    """Add language fields to base schema classes"""
    base_schema_file = Path('app/core/schemas/base.py')
    
    if not base_schema_file.exists():
        print(f"Error: {base_schema_file} does not exist")
        return False
    
    content = base_schema_file.read_text()
    
    # Add fields to DescriptionSchema class
    desc_schema_marker = "description_fr: Optional[str] = None"
    if desc_schema_marker in content:
        new_desc_fields = []
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            new_desc_fields.append(f"    description_{lang_code}: Optional[str] = None")
        
        # Insert new fields after the french field
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip() == desc_schema_marker:
                for new_field in new_desc_fields:
                    new_lines.append(new_field)
        
        content = '\n'.join(new_lines)
    
    # Add fields to DescriptionExcludeSchema class
    desc_exclude_marker = "description_fr: Optional[str] = Field(exclude=True)"
    if desc_exclude_marker in content:
        new_desc_exclude_fields = []
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            new_desc_exclude_fields.append(f"    description_{lang_code}: Optional[str] = Field(exclude=True)")
        
        # Insert new fields after the french field
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip() == desc_exclude_marker:
                for new_field in new_desc_exclude_fields:
                    new_lines.append(new_field)
        
        content = '\n'.join(new_lines)
    
    # Add fields to NameSchema class
    name_schema_marker = "name_fr: Optional[str] = None"
    if name_schema_marker in content:
        new_name_fields = []
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            new_name_fields.append(f"    name_{lang_code}: Optional[str] = None")
        
        # Insert new fields after the french field
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip() == name_schema_marker:
                for new_field in new_name_fields:
                    new_lines.append(new_field)
        
        content = '\n'.join(new_lines)
    
    # Add fields to NameExcludeSchema class
    name_exclude_marker = "name_fr: Optional[str] = Field(exclude=True)"
    if name_exclude_marker in content:
        new_name_exclude_fields = []
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            new_name_exclude_fields.append(f"    name_{lang_code}: Optional[str] = Field(exclude=True)")
        
        # Insert new fields after the french field
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if line.strip() == name_exclude_marker:
                for new_field in new_name_exclude_fields:
                    new_lines.append(new_field)
        
        content = '\n'.join(new_lines)
    
    base_schema_file.write_text(content)
    print(f"Added language fields to base schemas for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Add Spanish and Chinese language codes
    add_language_to_base_schemas(['es', 'cn'])