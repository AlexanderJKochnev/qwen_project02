# Translation Service

This module provides automatic translation functionality for database models with multilingual support.

## Features

- Automatic translation of `name` field to `name_ru` and `name_fr` fields
- Special handling for Russian noun cases (especially for Food model)
- Bulk translation for all existing records
- Integration with model creation and update operations
- Support for additional languages

## Models Supported

The translation service works with the following models:
- Country
- Region
- Subregion
- Category
- Subcategory
- Food
- Varietal

## How It Works

### 1. Automatic Translation on Create/Update

The translation functionality is integrated into the base service layer, so it automatically runs when:
- Creating new records (`create`, `get_or_create`, `update_or_create`, `create_relation`)
- Updating existing records (`patch`)

### 2. Bulk Translation

To translate all existing records in the database:

```bash
python /workspace/scripts/translate_db.py
```

To force update existing translations:
```bash
python /workspace/scripts/translate_db.py --force
```

### 3. Russian Noun Case Handling

For the Food model, the system:
- Translates English names to Russian and French
- Normalizes existing Russian translations to nominative case singular form (using pymorphy2)
- Preserves existing translations unless force update is used

## Implementation Details

### Translation Dictionaries

The service uses predefined translation dictionaries for each model type:
- Countries: France → Франция / France
- Regions: Bordeaux → Бордо / Bordeaux
- Foods: Cheese → Сыр / Fromage
- Varietals: Cabernet Sauvignon → Каберне Совиньон / Cabernet Sauvignon

### Language Support

Currently supports:
- Russian (`name_ru`)
- French (`name_fr`)

Additional languages can be added by:
1. Adding language code to `language_codes` mapping in `translator.py`
2. Adding translations to the dictionaries
3. Adding the appropriate field to the model's base class

### Architecture

- `translator.py`: Main translation service with dictionaries and logic
- `model_mixin.py`: Mixin class for manual integration and utility functions
- `bulk_translator.py`: Script for translating all records in the database
- Service layer integration: Automatic translation in base service methods

## Requirements

- `pymorphy2` (for Russian noun case normalization) - optional

## Integration

The translation is automatically integrated into the service layer through the `translate_model_instance` function called in:
- `create()`
- `get_or_create()`
- `update_or_create()`
- `create_relation()`
- `patch()`

## Usage in Application

When creating or updating records through the standard service layer, translations will be applied automatically if:
1. The `name` field exists and is not empty
2. The target language field (`name_ru`, `name_fr`) is empty (or it's a Food model requiring case normalization)
3. A translation exists in the dictionary for the specific term and model type