#!/usr/bin/env python3
"""
Script to remove language fields from form components
"""
from pathlib import Path
import re

def remove_language_from_forms(lang_codes: list):
    """Remove language fields from form components in preact_front"""
    form_files = [
        Path('preact_front/src/pages/HandbookCreateForm.tsx'),
        Path('preact_front/src/pages/HandbookUpdateForm.tsx'),
        Path('preact_front/src/pages/ItemCreateForm.tsx'),
        Path('preact_front/src/pages/ItemUpdateForm.tsx')
    ]
    
    for form_file in form_files:
        if not form_file.exists():
            print(f"Warning: {form_file} does not exist, skipping...")
            continue
        
        content = form_file.read_text()
        
        # Remove fields from the formData initialization
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            # Remove name field
            name_pattern = rf"(\s+)name_{lang_code}: ''(?:,|\n)"
            content = re.sub(name_pattern, r'\1', content)
            
            # Remove description field
            desc_pattern = rf"(\s+)description_{lang_code}: ''(?:,|\n)"
            content = re.sub(desc_pattern, r'\1', content)
        
        # Remove fields from useEffect in update forms
        if 'HandbookUpdateForm' in str(form_file) or 'ItemUpdateForm' in str(form_file):
            for lang in lang_codes:
                lang_code = 'zh' if lang == 'cn' else lang
                # Remove name field from useEffect
                useEffect_name_pattern = rf"(\s+)name_{lang_code}: data\.name_{lang_code} \|\| ''(?:,|\n)"
                content = re.sub(useEffect_name_pattern, r'\1', content)
                
                # Remove description field from useEffect
                useEffect_desc_pattern = rf"(\s+)description_{lang_code}: data\.description_{lang_code} \|\| ''(?:,|\n)"
                content = re.sub(useEffect_desc_pattern, r'\1', content)
        
        form_file.write_text(content)
        print(f"Removed language fields from {form_file.name} for: {', '.join(lang_codes)}")
    
    return True

if __name__ == "__main__":
    # Remove Spanish and Chinese language codes
    remove_language_from_forms(['es', 'cn'])