#!/usr/bin/env python3
"""
Script to add language fields to form components
"""
from pathlib import Path

def add_language_to_forms(lang_codes: list):
    """Add language fields to form components in preact_front"""
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
        
        # Add fields to the formData initialization
        # Look for the pattern with existing language fields
        import re
        
        # Pattern to match the state initialization block
        pattern = r'(\s*name: \'\',[^\}]*?)(\s*name_fr: \'\',[^\n]*\n)'
        replacement = r'\1\2'
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            replacement += f'    name_{lang_code}: \'\',\n'
        
        content = re.sub(pattern, replacement, content)
        
        # Also update the description fields
        desc_pattern = r'(\s*description: \'\',[^\}]*?)(\s*description_fr: \'\',[^\n]*\n)'
        desc_replacement = r'\1\2'
        for lang in lang_codes:
            lang_code = 'zh' if lang == 'cn' else lang
            desc_replacement += f'    description_{lang_code}: \'\',\n'
        
        content = re.sub(desc_pattern, desc_replacement, content)
        
        # Update the initial loading state in update forms
        if 'HandbookUpdateForm' in str(form_file) or 'ItemUpdateForm' in str(form_file):
            # Look for the setFormData in useEffect
            useEffect_pattern = r'(name_ru: data\.name_ru \|\| \'\',[^\}]*?)(\s*name_fr: data\.name_fr \|\| \'\',[^\n]*\n)'
            useEffect_replacement = r'\1\2'
            for lang in lang_codes:
                lang_code = 'zh' if lang == 'cn' else lang
                useEffect_replacement += f'        name_{lang_code}: data.name_{lang_code} || \'\',\n'
            
            content = re.sub(useEffect_pattern, useEffect_replacement, content)
            
            # Also update the description fields in useEffect
            desc_useEffect_pattern = r'(description_ru: data\.description_ru \|\| \'\',[^\}]*?)(\s*description_fr: data\.description_fr \|\| \'\',[^\n]*\n)'
            desc_useEffect_replacement = r'\1\2'
            for lang in lang_codes:
                lang_code = 'zh' if lang == 'cn' else lang
                desc_useEffect_replacement += f'        description_{lang_code}: data.description_{lang_code} || \'\',\n'
            
            content = re.sub(desc_useEffect_pattern, desc_useEffect_replacement, content)
        
        form_file.write_text(content)
        print(f"Added language fields to {form_file.name} for: {', '.join(lang_codes)}")
    
    return True

if __name__ == "__main__":
    # Add Spanish and Chinese language codes
    add_language_to_forms(['es', 'cn'])