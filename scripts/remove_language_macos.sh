#!/bin/bash

# Script to remove a language from the codebase (macOS version)
# Usage: ./remove_language_macos.sh <lang_code>
# Example: ./remove_language_macos.sh es

if [ $# -ne 1 ]; then
    echo "Usage: $0 <lang_code>"
    echo "Example: $0 es"
    exit 1
fi

LANG_CODE=$1

# Validate language code (2 characters)
if [[ ! $LANG_CODE =~ ^[a-z]{2}$ ]]; then
    echo "Error: Language code must be 2 lowercase letters"
    exit 1
fi

echo "Removing language: $LANG_CODE"

# 1. Update .env file
if [ -f .env ]; then
    sed -i '' "s/,$LANG_CODE//g; s/$LANG_CODE,//g; s/ $LANG_CODE//g; s/$LANG_CODE //g" .env
    echo "Updated .env file"
else
    echo "Warning: .env file not found"
fi

# 2. Update app/core/config/project_config.py
if [ -f app/core/config/project_config.py ]; then
    sed -i '' "s/, $LANG_CODE//g; s/$LANG_CODE, //g" app/core/config/project_config.py
    echo "Updated app/core/config/project_config.py"
else
    echo "Warning: app/core/config/project_config.py not found"
fi

# 3. Update app/core/models/base_model.py
if [ -f app/core/models/base_model.py ]; then
    # Remove description field from BaseDescription class
    sed -i '' "/description_$LANG_CODE: Mapped\[descr\]/d" app/core/models/base_model.py
    
    # Remove name field from BaseLang class
    sed -i '' "/name_$LANG_CODE: Mapped\[str_null_true\]/d" app/core/models/base_model.py
    echo "Updated app/core/models/base_model.py"
else
    echo "Warning: app/core/models/base_model.py not found"
fi

# 4. Update app/support/drink/model.py
if [ -f app/support/drink/model.py ]; then
    # Remove fields from Lang class
    sed -i '' "/title_$LANG_CODE: Mapped\[str_null_true\]/d" app/support/drink/model.py
    sed -i '' "/subtitle_$LANG_CODE: Mapped\[str_null_true\]/d" app/support/drink/model.py
    sed -i '' "/description_$LANG_CODE: Mapped\[descr\]/d" app/support/drink/model.py
    sed -i '' "/recommendation_$LANG_CODE: Mapped\[descr\]/d" app/support/drink/model.py
    sed -i '' "/madeof_$LANG_CODE: Mapped\[descr\]/d" app/support/drink/model.py

    # Update trigram index query
    sed -i '' "s/coalesce(title_$LANG_CODE, '') || ' ' || //g; s/ || ' ' || coalesce(title_$LANG_CODE, '')//g" app/support/drink/model.py
    sed -i '' "s/coalesce(subtitle_$LANG_CODE, '') || ' ' || //g; s/ || ' ' || coalesce(subtitle_$LANG_CODE, '')//g" app/support/drink/model.py
    sed -i '' "s/coalesce(description_$LANG_CODE, '') || ' ' || //g; s/ || ' ' || coalesce(description_$LANG_CODE, '')//g" app/support/drink/model.py
    sed -i '' "s/coalesce(recommendation_$LANG_CODE, '') || ' ' || //g; s/ || ' ' || coalesce(recommendation_$LANG_CODE, '')//g" app/support/drink/model.py
    sed -i '' "s/ || ' ' || coalesce(madeof_$LANG_CODE, '')//g; s/coalesce(madeof_$LANG_CODE, '') || ' ' || //g" app/support/drink/model.py
    
    echo "Updated app/support/drink/model.py"
else
    echo "Warning: app/support/drink/model.py not found"
fi

# 5. Update app/core/utils/translation_utils.py
if [ -f app/core/utils/translation_utils.py ]; then
    # Remove fields from get_localized_fields function
    sed -i '' "s/        'name_$LANG_CODE',//g; s/'name_$LANG_CODE', //g; s/, 'name_$LANG_CODE'//g" app/core/utils/translation_utils.py
    sed -i '' "s/        'description_$LANG_CODE',//g; s/'description_$LANG_CODE', //g; s/, 'description_$LANG_CODE'//g" app/core/utils/translation_utils.py
    sed -i '' "s/        'title_$LANG_CODE',//g; s/'title_$LANG_CODE', //g; s/, 'title_$LANG_CODE'//g" app/core/utils/translation_utils.py
    sed -i '' "s/        'subtitle_$LANG_CODE',//g; s/'subtitle_$LANG_CODE', //g; s/, 'subtitle_$LANG_CODE'//g" app/core/utils/translation_utils.py
    
    # Remove from get_field_language function
    sed -i '' "/elif field_name.endswith('_$LANG_CODE'):/d; /return '$LANG_CODE'/d" app/core/utils/translation_utils.py
    
    # Remove from get_base_field_name function
    sed -i '' "s/('_ru', '_fr', '_$LANG_CODE')/('_ru', '_fr')/g; s/('_$LANG_CODE')//g" app/core/utils/translation_utils.py
    
    # Remove from fill_missing_translations function
    sed -i '' "s/, '$LANG_CODE'//g; s/'$LANG_CODE', //g" app/core/utils/translation_utils.py
    
    echo "Updated app/core/utils/translation_utils.py"
else
    echo "Warning: app/core/utils/translation_utils.py not found"
fi

# 6. Update app/core/schemas/lang_schemas.py
if [ -f app/core/schemas/lang_schemas.py ]; then
    # Remove language schema classes (this is more complex, we'll remove the class definitions)
    sed -i '' "/class ListView${LANG_CODE^^}(ListView):/,/^$/d" app/core/schemas/lang_schemas.py
    sed -i '' "/class DetailView${LANG_CODE^^}(DetailView):/,/^$/d" app/core/schemas/lang_schemas.py
    echo "Updated app/core/schemas/lang_schemas.py"
else
    echo "Warning: app/core/schemas/lang_schemas.py not found"
fi

# 7. Update preact_front/src/contexts/LanguageContext.tsx
if [ -f preact_front/src/contexts/LanguageContext.tsx ]; then
    # Remove language from availableLanguages in the context
    sed -i '' "s/, '$LANG_CODE'//g; s/'$LANG_CODE', //g" preact_front/src/contexts/LanguageContext.tsx
    
    # Remove placeholder comment if we added one
    sed -i '' "/Add translations for $LANG_CODE/d" preact_front/src/contexts/LanguageContext.tsx
    
    echo "Updated preact_front/src/contexts/LanguageContext.tsx"
else
    echo "Warning: preact_front/src/contexts/LanguageContext.tsx not found"
fi

# 8. Update preact_front/src/types/drink.ts
if [ -f preact_front/src/types/drink.ts ]; then
    # Remove language field from DrinkReadFlat interface
    sed -i '' "/  $LANG_CODE: LangFields;/d" preact_front/src/types/drink.ts
    echo "Updated preact_front/src/types/drink.ts"
else
    echo "Warning: preact_front/src/types/drink.ts not found"
fi

echo "Language $LANG_CODE has been removed from the codebase!"
echo "Remember to run database migrations and recreate trigram indexes if needed."