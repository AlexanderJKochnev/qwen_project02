# Language Modifications Documentation

This document describes all the places in the codebase where language codes need to be modified when adding or removing languages.

## Files to Modify

### Backend Files

1. **`.env`**
   - Variable: `LANGS=en,ru,fr`
   - Add/Remove language codes from the comma-separated list

2. **`app/core/config/project_config.py`**
   - Line 25: `LANGS: str = "en, ru, fr"`
   - Update the default language list

3. **`app/core/models/base_model.py`**
   - Class `BaseDescription`: Add/Remove language-specific description fields
   - Class `BaseLang`: Add/Remove language-specific name fields

4. **`app/support/drink/model.py`**
   - Class `Lang`: Add/Remove language-specific fields for title, subtitle, description, recommendation, madeof
   - Trigram index query: Update to include new language fields

5. **`app/core/utils/translation_utils.py`**
   - Function `get_localized_fields()`: Add/Remove fields from the list
   - Functions `get_field_language()`, `get_base_field_name()`: Update logic for new language codes

6. **`app/core/schemas/lang_schemas.py`**
   - Add/Remove language-specific ListView and DetailView classes
   - Update display_name and display_description methods

### Frontend Files

7. **`preact_front/src/contexts/LanguageContext.tsx`**
   - Available languages list: Update the default list and translation dictionaries
   - Add new language translations to the `translations` object

8. **`preact_front/src/types/drink.ts`**
   - Interface `DrinkReadFlat`: Add/Remove language fields in the en, ru, fr, etc. structure

### Additional Considerations

- Database migrations may be needed after adding new language fields
- Trigram indexes may need to be recreated after adding language fields
- Testing files may also reference language codes and should be checked