#!/bin/bash

# Script to add a language to the codebase (macOS version)
# Usage: ./add_language_macos.sh <lang_code>
# Example: ./add_language_macos.sh es

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

echo "Adding language: $LANG_CODE"

# 1. Update .env file
if [ -f .env ]; then
    sed -i '' "s/LANGS=\(.*\)/LANGS=\1,$LANG_CODE/" .env
    echo "Updated .env file"
else
    echo "Warning: .env file not found"
fi

# 2. Update app/core/config/project_config.py
if [ -f app/core/config/project_config.py ]; then
    sed -i '' "s/LANGS: str = \"\(.*\)\"/LANGS: str = \"\1, $LANG_CODE\"/" app/core/config/project_config.py
    echo "Updated app/core/config/project_config.py"
else
    echo "Warning: app/core/config/project_config.py not found"
fi

# 3. Update app/core/models/base_model.py
if [ -f app/core/models/base_model.py ]; then
    # Add description field to BaseDescription class
    sed -i '' "/description_fr: Mapped\[descr\]/a\\
    description_$LANG_CODE: Mapped[descr]
" app/core/models/base_model.py
    
    # Add name field to BaseLang class
    sed -i '' "/name_fr: Mapped\[str_null_true\]/a\\
    name_$LANG_CODE: Mapped[str_null_true]
" app/core/models/base_model.py
    echo "Updated app/core/models/base_model.py"
else
    echo "Warning: app/core/models/base_model.py not found"
fi

# 4. Update app/support/drink/model.py
if [ -f app/support/drink/model.py ]; then
    # Add fields to Lang class
    sed -i '' "/title_fr: Mapped\[str_null_true\]/a\\
    title_$LANG_CODE: Mapped[str_null_true]
" app/support/drink/model.py
    
    sed -i '' "/subtitle_fr: Mapped\[str_null_true\]/a\\
    subtitle_$LANG_CODE: Mapped[str_null_true]
" app/support/drink/model.py
    
    sed -i '' "/description_fr: Mapped\[descr\]/a\\
    description_$LANG_CODE: Mapped[descr]
" app/support/drink/model.py
    
    sed -i '' "/recommendation_fr: Mapped\[descr\]/a\\
    recommendation_$LANG_CODE: Mapped[descr]
" app/support/drink/model.py
    
    sed -i '' "/madeof_fr: Mapped\[descr\]/a\\
    madeof_$LANG_CODE: Mapped[descr]
" app/support/drink/model.py

    # Update trigram index query
    sed -i '' "s/\(coalesce(title_fr, '') || ' ' ||\)/\1 coalesce(title_$LANG_CODE, '') || ' ' || /" app/support/drink/model.py
    sed -i '' "s/\(coalesce(subtitle_fr, '') || ' ' ||\)/\1 coalesce(subtitle_$LANG_CODE, '') || ' ' || /" app/support/drink/model.py
    sed -i '' "s/\(coalesce(description_fr, '') || ' ' ||\)/\1 coalesce(description_$LANG_CODE, '') || ' ' || /" app/support/drink/model.py
    sed -i '' "s/\(coalesce(recommendation_fr, '') || ' ' ||\)/\1 coalesce(recommendation_$LANG_CODE, '') || ' ' || /" app/support/drink/model.py
    sed -i '' "s/\(coalesce(madeof_fr, ''))\)/\1 || ' ' || coalesce(madeof_$LANG_CODE, ''))/g" app/support/drink/model.py
    
    echo "Updated app/support/drink/model.py"
else
    echo "Warning: app/support/drink/model.py not found"
fi

# 5. Update app/core/utils/translation_utils.py
if [ -f app/core/utils/translation_utils.py ]; then
    # Add fields to get_localized_fields function
    sed -i '' "s/'name_fr', 'name_ru'/&,\n        'name_$LANG_CODE'/" app/core/utils/translation_utils.py
    sed -i '' "s/'description_fr', 'description_ru'/&,\n        'description_$LANG_CODE'/" app/core/utils/translation_utils.py
    sed -i '' "s/'title_fr', 'title_ru'/&,\n        'title_$LANG_CODE'/" app/core/utils/translation_utils.py
    sed -i '' "s/'subtitle_fr', 'subtitle_ru'/&,\n        'subtitle_$LANG_CODE'/" app/core/utils/translation_utils.py
    
    # Update get_field_language function
    sed -i '' "/elif field_name.endswith('_fr'):/a\\
    elif field_name.endswith('_$LANG_CODE'):\\
        return '$LANG_CODE'
" app/core/utils/translation_utils.py
    
    # Update get_base_field_name function
    sed -i '' "s/('_ru', '_fr')/('_ru', '_fr', '_$LANG_CODE')/" app/core/utils/translation_utils.py
    
    # Update fill_missing_translations function
    sed -i '' "s/\['en', 'fr', 'ru'\]/['en', 'fr', 'ru', '$LANG_CODE']/" app/core/utils/translation_utils.py
    
    echo "Updated app/core/utils/translation_utils.py"
else
    echo "Warning: app/core/utils/translation_utils.py not found"
fi

# 6. Update app/core/schemas/lang_schemas.py
if [ -f app/core/schemas/lang_schemas.py ]; then
    # Add new language schema classes (this is more complex, so we'll add at the end)
    cat >> app/core/schemas/lang_schemas.py << EOF

class ListView${LANG_CODE^^}(ListView):
    @computed_field(description='${LANG_CODE^^}',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
        \"\"\"Возвращает первое непустое значение из name, name_ru, name_fr и других языков\"\"\"
        return self.name_$LANG_CODE or self.name or self.name_ru or self.name_fr or ""


class DetailView${LANG_CODE^^}(DetailView):
    @computed_field(description='${LANG_CODE^^}',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
        \"\"\"Возвращает первое непустое значение из name, name_ru, name_fr и других языков\"\"\"
        return self.name_$LANG_CODE or self.name or self.name_ru or self.name_fr or ""

    @computed_field(description='${LANG_CODE^^}',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_description(self) -> str:
        return self.description_$LANG_CODE or self.description or self.description_ru or self.description_fr or ""
EOF
    echo "Updated app/core/schemas/lang_schemas.py"
else
    echo "Warning: app/core/schemas/lang_schemas.py not found"
fi

# 7. Update preact_front/src/contexts/LanguageContext.tsx
if [ -f preact_front/src/contexts/LanguageContext.tsx ]; then
    # Add language to availableLanguages in the context
    sed -i '' "s/\['en', 'ru', 'fr'\]/['en', 'ru', 'fr', '$LANG_CODE']/" preact_front/src/contexts/LanguageContext.tsx
    
    # Add translations for the new language (simplified - just add the language object)
    # This is more complex, so we'll just add a placeholder comment
    sed -i '' "/export type Language = string;/a\\
// Add translations for $LANG_CODE here if needed
" preact_front/src/contexts/LanguageContext.tsx
    
    echo "Updated preact_front/src/contexts/LanguageContext.tsx"
else
    echo "Warning: preact_front/src/contexts/LanguageContext.tsx not found"
fi

# 8. Update preact_front/src/types/drink.ts
if [ -f preact_front/src/types/drink.ts ]; then
    # Add language field to DrinkReadFlat interface
    sed -i '' "s/  fr: LangFields;/  fr: LangFields;\\
  $LANG_CODE: LangFields;/g" preact_front/src/types/drink.ts
    echo "Updated preact_front/src/types/drink.ts"
else
    echo "Warning: preact_front/src/types/drink.ts not found"
fi

echo "Language $LANG_CODE has been added to the codebase!"
echo "Remember to run database migrations and recreate trigram indexes if needed."