#!/usr/bin/env python3
"""
Script to add language fields to lang schemas
"""
from pathlib import Path

def add_language_to_lang_schemas(lang_codes: list):
    """Add language fields to lang schema classes"""
    lang_schema_file = Path('app/core/schemas/lang_schemas.py')
    
    if not lang_schema_file.exists():
        print(f"Error: {lang_schema_file} does not exist")
        return False
    
    content = lang_schema_file.read_text()
    
    # Add new language schema classes
    for lang in lang_codes:
        lang_code = 'zh' if lang == 'cn' else lang  # Use 'zh' for Chinese
        lang_name = 'Chinese' if lang == 'cn' else lang.capitalize()
        
        # Create new schema classes for the language
        new_schema_classes = f"""
class ListView{lang_name.capitalize()}(ListView):
    @computed_field(description='Name',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
        \"\"\"Возвращает первое непустое значение из name, name_ru, name_fr и name_{lang_code}\"\"\"
        return self.name_{lang_code} or self.name or self.name_ru or self.name_fr or ""


class DetailView{lang_name.capitalize()}(DetailView):
    @computed_field(description='Name',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
        \"\"\"Возвращает первое непустое значение из name, name_ru, name_fr и name_{lang_code}\"\"\"
        return self.name_{lang_code} or self.name or self.name_ru or self.name_fr or ""

    @computed_field(description='Name',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_description(self) -> str:
        return self.description_{lang_code} or self.description or self.description_ru or self.description_fr or ""
"""
        
        # Add the new classes at the end of the file
        content += new_schema_classes
    
    lang_schema_file.write_text(content)
    print(f"Added language schema classes for: {', '.join(lang_codes)}")
    return True

if __name__ == "__main__":
    # Add Spanish and Chinese language codes
    add_language_to_lang_schemas(['es', 'cn'])