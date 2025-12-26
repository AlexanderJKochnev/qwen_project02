#!/usr/bin/env python3
"""
Script to remove language fields from lang schemas
"""
from pathlib import Path

def remove_language_from_lang_schemas(lang_codes: list):
    """Remove language fields from lang schema classes"""
    lang_schema_file = Path('app/core/schemas/lang_schemas.py')
    
    if not lang_schema_file.exists():
        print(f"Error: {lang_schema_file} does not exist")
        return False
    
    content = lang_schema_file.read_text()
    
    # Remove new language schema classes
    for lang in lang_codes:
        lang_name = 'Chinese' if lang == 'cn' else lang.capitalize()
        
        # Remove the class definitions
        import re
        # Pattern to match the entire class definition (from one class to the next)
        # Match ListView<Lang> class
        list_view_pattern = rf"class ListView{lang_name.capitalize()}\(ListView\):.*?(?=class \w+ListView|class \w+DetailView|class ListViewRu|class DetailViewRu|class ListViewFr|class DetailViewFr|class ListViewEn|class DetailViewEn|$)"
        content = re.sub(list_view_pattern, "", content, flags=re.DOTALL)
        
        # Match DetailView<Lang> class
        detail_view_pattern = rf"class DetailView{lang_name.capitalize()}\(DetailView\):.*?(?=class \w+ListView|class \w+DetailView|class ListViewRu|class DetailViewRu|class ListViewFr|class DetailViewFr|class ListViewEn|class DetailViewEn|$)"
        content = re.sub(detail_view_pattern, "", content, flags=re.DOTALL)
    
    lang_schema_file.write_text(content)
    print(f"Removed language schema classes for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Remove Spanish and Chinese language codes
    remove_language_from_lang_schemas(['es', 'cn'])