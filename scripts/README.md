# Language Management Scripts

This directory contains scripts for adding and removing languages from the codebase.

## Available Scripts

### Adding Languages
- `add_language_macos.sh` - Add a language to the codebase (macOS version)
- `add_language_linux.sh` - Add a language to the codebase (Linux Debian version)

### Removing Languages
- `remove_language_macos.sh` - Remove a language from the codebase (macOS version)
- `remove_language_linux.sh` - Remove a language from the codebase (Linux Debian version)

## Usage

### Adding a Language
```bash
# For macOS
./scripts/add_language_macos.sh <lang_code>

# For Linux Debian
./scripts/add_language_linux.sh <lang_code>
```

Example:
```bash
./scripts/add_language_linux.sh es  # Adds Spanish language support
```

### Removing a Language
```bash
# For macOS
./scripts/remove_language_macos.sh <lang_code>

# For Linux Debian
./scripts/remove_language_linux.sh <lang_code>
```

Example:
```bash
./scripts/remove_language_linux.sh es  # Removes Spanish language support
```

## What the Scripts Do

The scripts modify the following files in the codebase:

1. **`.env`** - Updates the `LANGS` variable with the new language codes
2. **`app/core/config/project_config.py`** - Updates the default language list
3. **`app/core/models/base_model.py`** - Adds/Removes language-specific fields in BaseDescription and BaseLang classes
4. **`app/support/drink/model.py`** - Adds/Removes language-specific fields in the Lang class and updates trigram index queries
5. **`app/core/utils/translation_utils.py`** - Updates translation utility functions to include/exclude the language
6. **`app/core/schemas/lang_schemas.py`** - Adds/Removes language-specific schema classes
7. **`preact_front/src/contexts/LanguageContext.tsx`** - Updates available languages in the frontend context
8. **`preact_front/src/types/drink.ts`** - Updates the DrinkReadFlat interface with language fields

## Important Notes

- The language code should be a 2-letter lowercase code (e.g., `es`, `fr`, `de`)
- After adding a language, you may need to run database migrations
- After adding a language, you may need to recreate trigram indexes if they exist
- The scripts do not modify test files, which may need manual updates
- Frontend translation dictionaries are not automatically updated and may need manual addition