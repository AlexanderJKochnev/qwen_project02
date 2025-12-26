#!/bin/bash
# Script to remove language support from the application
# Usage: ./remove_language.sh <lang_code>
# Example: ./remove_language.sh es

if [ $# -ne 1 ]; then
    echo "Usage: $0 <lang_code>"
    echo "Example: $0 es"
    exit 1
fi

LANG_CODE=$1

echo "Removing language: $LANG_CODE"

# Update .env file
if [ -f .env ]; then
    sed -i "s/,${LANG_CODE}//g; s/${LANG_CODE},//g; s/${LANG_CODE}//g" .env
    # Clean up any double commas or trailing commas
    sed -i "s/,,/,/g; s/,$//" .env
    echo "Updated .env file"
fi

# Update project config
if [ -f app/core/config/project_config.py ]; then
    sed -i "s/, ${LANG_CODE}//g; s/${LANG_CODE}, //g; s/${LANG_CODE}//g" app/core/config/project_config.py
    # Clean up any double commas or trailing commas
    sed -i "s/,,/,/g; s/,$//" app/core/config/project_config.py
    echo "Updated project config"
fi

# Update base model - BaseDescription class
if [ -f app/core/models/base_model.py ]; then
    # Remove BaseDescription field
    sed -i "/description_${LANG_CODE}: Mapped\[descr\]/d" app/core/models/base_model.py
    echo "Updated BaseDescription in base_model.py"
    
    # Remove BaseLang field
    sed -i "/name_${LANG_CODE}: Mapped\[str_null_true\]/d" app/core/models/base_model.py
    echo "Updated BaseLang in base_model.py"
fi

# Update drink model - Lang class
if [ -f app/support/drink/model.py ]; then
    # Remove fields from Lang class
    sed -i "/title_${LANG_CODE}: Mapped\[str_null_true\]/d" app/support/drink/model.py
    sed -i "/subtitle_${LANG_CODE}: Mapped\[str_null_true\]/d" app/support/drink/model.py
    sed -i "/description_${LANG_CODE}: Mapped\[descr\]/d" app/support/drink/model.py
    sed -i "/recommendation_${LANG_CODE}: Mapped\[descr\]/d" app/support/drink/model.py
    sed -i "/madeof_${LANG_CODE}: Mapped\[descr\]/d" app/support/drink/model.py
    echo "Updated Lang class in drink model"
    
    # Remove from SQL index in the model (inside create_gin_index_sql)
    sed -i "/coalesce(title_${LANG_CODE}, '')/d" app/support/drink/model.py
    sed -i "/coalesce(subtitle_${LANG_CODE}, '')/d" app/support/drink/model.py
    sed -i "/coalesce(description_${LANG_CODE}, '')/d" app/support/drink/model.py
    sed -i "/coalesce(recommendation_${LANG_CODE}, '')/d" app/support/drink/model.py
    sed -i "/coalesce(madeof_${LANG_CODE}, '')/d" app/support/drink/model.py
    echo "Updated SQL index in drink model"
fi

# Update translation utilities
if [ -f app/core/utils/translation_utils.py ]; then
    # Remove from get_localized_fields function
    sed -i "s/, 'name_${LANG_CODE}'//g; s/'name_${LANG_CODE}', //g; s/'name_${LANG_CODE}'//g" app/core/utils/translation_utils.py
    sed -i "s/, 'description_${LANG_CODE}'//g; s/'description_${LANG_CODE}', //g; s/'description_${LANG_CODE}'//g" app/core/utils/translation_utils.py
    sed -i "s/, 'title_${LANG_CODE}'//g; s/'title_${LANG_CODE}', //g; s/'title_${LANG_CODE}'//g" app/core/utils/translation_utils.py
    sed -i "s/, 'subtitle_${LANG_CODE}'//g; s/'subtitle_${LANG_CODE}', //g; s/'subtitle_${LANG_CODE}'//g" app/core/utils/translation_utils.py
    echo "Updated translation_utils.py localized fields"
    
    # Remove from get_field_language function
    sed -i "/elif field_name.endswith('_${LANG_CODE}'):/d; /return '${LANG_CODE}'/d" app/core/utils/translation_utils.py
    echo "Updated get_field_language function"
    
    # Remove from get_base_field_name function (no specific change needed for this one)
    sed -i "s/ or field_name.endswith('_${LANG_CODE}')//g" app/core/utils/translation_utils.py
    echo "Updated get_base_field_name function"
    
    # Remove from fill_missing_translations priority list
    sed -i "s/, '${LANG_CODE}'//g; s/'${LANG_CODE}', //g; s/'${LANG_CODE}'//g" app/core/utils/translation_utils.py
    # Clean up any double commas or trailing commas
    sed -i "s/,,/,/g; s/,$//" app/core/utils/translation_utils.py
    echo "Updated fill_missing_translations priority list"
fi

# Update SQL index script
if [ -f scripts/create_index.sql ]; then
    sed -i "/coalesce(title_${LANG_CODE}, '')/d" scripts/create_index.sql
    sed -i "/coalesce(subtitle_${LANG_CODE}, '')/d" scripts/create_index.sql
    sed -i "/coalesce(description_${LANG_CODE}, '')/d" scripts/create_index.sql
    sed -i "/coalesce(recommendation_${LANG_CODE}, '')/d" scripts/create_index.sql
    sed -i "/coalesce(madeof_${LANG_CODE}, '')/d" scripts/create_index.sql
    echo "Updated create_index.sql"
fi

# Remove language schema classes
if [ -f app/core/schemas/lang_schemas.py ]; then
    # Remove ListView and DetailView for the language
    sed -i "/class ListView${LANG_CODE^}/,/^$/d" app/core/schemas/lang_schemas.py
    sed -i "/class DetailView${LANG_CODE^}/,/^$/d" app/core/schemas/lang_schemas.py
    echo "Removed ${LANG_CODE} schema classes from lang_schemas.py"
fi

# Update preact frontend - LanguageContext.tsx
if [ -f preact_front/src/contexts/LanguageContext.tsx ]; then
    # Remove language from availableLanguages initialization
    sed -i "s/, '${LANG_CODE}'//g; s/'${LANG_CODE}', //g; s/'${LANG_CODE}'//g" preact_front/src/contexts/LanguageContext.tsx
    # Clean up any double commas or trailing commas
    sed -i "s/,,/,/g; s/,$//" preact_front/src/contexts/LanguageContext.tsx
    
    # Remove the entire language section from translations object
    sed -i "/  ${LANG_CODE}: {/,/  },/d" preact_front/src/contexts/LanguageContext.tsx
    echo "Updated LanguageContext.tsx to remove ${LANG_CODE} language section"
fi

# Update translation test
if [ -f tests/qwen/test_translation.py ]; then
    sed -i "/'name_${LANG_CODE}': None,/d" tests/qwen/test_translation.py
    sed -i "/'description_${LANG_CODE}': None,/d" tests/qwen/test_translation.py
    sed -i "/'title_${LANG_CODE}': None,/d" tests/qwen/test_translation.py
    echo "Updated translation test file"
fi

echo "Language $LANG_CODE has been removed from the application!"