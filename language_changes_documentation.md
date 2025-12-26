# Language Support Changes Documentation

This document outlines all the modules, classes, methods, functions, and variables that are affected when adding or removing language support in the application.

## Backend (Python)

### 1. Configuration Files
- **File:** `.env`
  - **Variable:** `LANGS` - Contains comma-separated list of supported language codes
  - **Variable:** `DEFAULT_LANG` - Default language for the application

### 2. Core Configuration
- **File:** `app/core/config/project_config.py`
  - **Variable:** `LANGS` - Default value for supported languages
  - **Property:** `LANGUAGES` - Returns list of supported languages from settings
  - **Variable:** `DEFAULT_LANG` - Default language setting

### 3. Database Models
- **File:** `app/core/models/base_model.py`
  - **Class:** `BaseDescription` - Abstract base class containing localized description fields
    - **Field:** `description_<lang_code>` - Localized description fields for each language
  - **Class:** `BaseLang` - Abstract base class containing localized name fields (inherits from BaseDescription)
    - **Field:** `name_<lang_code>` - Localized name fields for each language

- **File:** `app/support/drink/model.py`
  - **Class:** `Lang` - Abstract base class containing localized fields for drink-related models
    - **Fields:** `title_<lang_code>` - Localized title fields
    - **Fields:** `subtitle_<lang_code>` - Localized subtitle fields
    - **Fields:** `description_<lang_code>` - Localized description fields
    - **Fields:** `recommendation_<lang_code>` - Localized recommendation fields
    - **Fields:** `madeof_<lang_code>` - Localized madeof fields
  - **SQL Index:** `create_gin_index_sql` - Trigram search index that includes all language fields
    - Contains `coalesce` calls for all language fields to enable full-text search across languages

### 4. Translation Utilities
- **File:** `app/core/utils/translation_utils.py`
  - **Function:** `get_localized_fields()` - Returns list of all localized field names that should be translated
    - Contains entries like: `name_<lang_code>`, `description_<lang_code>`, etc.
  - **Function:** `get_field_language(field_name)` - Extracts language code from field name
    - Contains conditions for each language code: `field_name.endswith('_<lang_code>')`
  - **Function:** `get_base_field_name(field_name)` - Gets the base field name without language suffix
    - Contains logic to handle all language suffixes: `field_name.endswith(('_ru', '_fr', '_<lang_code>'))`
  - **Function:** `fill_missing_translations(data)` - Fills missing translations in data dictionary
    - Contains priority list: `['en', 'fr', 'ru', '<lang_code>']` for translation source priority

### 5. Schema Definitions
- **File:** `app/core/schemas/lang_schemas.py`
  - **Class:** `ListView<LanguageName>` - Schema for list view with language-specific display
    - Contains `display_name` property that prioritizes language-specific fields
  - **Class:** `DetailView<LanguageName>` - Schema for detail view with language-specific display
    - Contains `display_name` and `display_description` properties that prioritize language-specific fields

### 6. API Endpoints
- **File:** `app/preact/get/router.py`
  - **Function:** `get_languages()` - Returns available languages from settings
    - Uses `settings.LANGUAGES` to return the list of supported languages

### 7. Database Indexes
- **File:** `scripts/create_index.sql`
  - **SQL Query:** GIN trigram index that includes all language fields for search functionality
  - Contains `coalesce` calls for all language fields to enable cross-language search

### 8. Tests
- **File:** `tests/qwen/test_translation.py`
  - Contains test data with language-specific fields for translation testing
  - Fields like: `name_<lang_code>`, `description_<lang_code>`, `title_<lang_code>`

## Frontend (Preact/TypeScript)

### 1. Language Context
- **File:** `preact_front/src/contexts/LanguageContext.tsx`
  - **Variable:** `availableLanguages` - Array of supported language codes
  - **Translations Object:** Contains language-specific translations for UI elements
    - Each language has its own section: `en: { ... }`, `ru: { ... }`, `fr: { ... }`, `<lang_code>: { ... }`
  - **Function:** `fetchAvailableLanguages()` - Fetches available languages from backend API
  - **Function:** `t(key)` - Translation function that uses current language

## Summary of Changes Required

When adding a new language (e.g., 'es' for Spanish):
1. Add language code to `.env` LANGS variable
2. Add language code to project config LANGS setting
3. Add language-specific fields to all relevant model classes
4. Update SQL indexes to include new language fields
5. Update translation utilities to recognize new language
6. Add schema classes for the new language
7. Add translations to frontend context
8. Update test data to include new language fields

When removing a language:
1. Remove language code from configuration
2. Remove language-specific fields from models
3. Update SQL indexes to exclude language fields
4. Remove language handling from utilities
5. Remove schema classes
6. Remove frontend translations
7. Remove language fields from test data

## Important Notes
- The language code should be a 2-letter ISO code (e.g., 'es', 'cn')
- Always maintain the same naming pattern: `<field_name>_<lang_code>`
- SQL indexes must be updated to maintain search functionality
- Frontend translations need to be provided for proper user experience
- After adding/removing languages, database migrations may be required to update table schemas