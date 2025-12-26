#!/bin/bash
# Script to add new language support to the application
# Usage: ./add_language.sh <lang_code> <lang_name>
# Example: ./add_language.sh es Spanish

if [ $# -ne 2 ]; then
    echo "Usage: $0 <lang_code> <lang_name>"
    echo "Example: $0 es Spanish"
    exit 1
fi

LANG_CODE=$1
LANG_NAME=$2

echo "Adding language: $LANG_CODE ($LANG_NAME)"

# Update .env file
if [ -f .env ]; then
    sed -i "s/LANGS=en,ru,fr/LANGS=en,ru,fr,$LANG_CODE/g" .env
    echo "Updated .env file"
fi

# Update project config
if [ -f app/core/config/project_config.py ]; then
    sed -i "s/LANGS: str = \"en, ru, fr\"/LANGS: str = \"en, ru, fr, $LANG_CODE\"/g" app/core/config/project_config.py
    echo "Updated project config"
fi

# Update base model - BaseDescription class
if [ -f app/core/models/base_model.py ]; then
    sed -i "/description_fr: Mapped\[descr\]/a\    description_${LANG_CODE}: Mapped[descr]" app/core/models/base_model.py
    echo "Updated BaseDescription in base_model.py"
    
    # Update BaseLang class
    sed -i "/name_fr: Mapped\[str_null_true\]/a\    name_${LANG_CODE}: Mapped[str_null_true]" app/core/models/base_model.py
    echo "Updated BaseLang in base_model.py"
fi

# Update drink model - Lang class
if [ -f app/support/drink/model.py ]; then
    # Add title field
    sed -i "/title_fr: Mapped\[str_null_true\]/a\    title_${LANG_CODE}: Mapped[str_null_true]" app/support/drink/model.py
    echo "Updated title in drink model"
    
    # Add subtitle field
    sed -i "/subtitle_fr: Mapped\[str_null_true\]/a\    subtitle_${LANG_CODE}: Mapped[str_null_true]" app/support/drink/model.py
    echo "Updated subtitle in drink model"
    
    # Add description field
    sed -i "/description_fr: Mapped\[descr\]/a\    description_${LANG_CODE}: Mapped[descr]" app/support/drink/model.py
    echo "Updated description in drink model"
    
    # Add recommendation field
    sed -i "/recommendation_fr: Mapped\[descr\]/a\    recommendation_${LANG_CODE}: Mapped[descr]" app/support/drink/model.py
    echo "Updated recommendation in drink model"
    
    # Add madeof field
    sed -i "/madeof_fr: Mapped\[descr\]/a\    madeof_${LANG_CODE}: Mapped[descr]" app/support/drink/model.py
    echo "Updated madeof in drink model"
    
    # Update SQL index in the model (find the index definition)
    sed -i "/coalesce(title_fr, '')/a\             coalesce(title_${LANG_CODE}, '') || ' ' ||" app/support/drink/model.py
    sed -i "/coalesce(subtitle_fr, '')/a\             coalesce(subtitle_${LANG_CODE}, '') || ' ' ||" app/support/drink/model.py
    sed -i "/coalesce(description_fr, '')/a\             coalesce(description_${LANG_CODE}, '') || ' ' ||" app/support/drink/model.py
    sed -i "/coalesce(recommendation_fr, '')/a\             coalesce(recommendation_${LANG_CODE}, '') || ' ' ||" app/support/drink/model.py
    sed -i "/coalesce(madeof_fr, ''))/a\             coalesce(madeof_${LANG_CODE}, ''))" app/support/drink/model.py
fi

# Update translation utilities
if [ -f app/core/utils/translation_utils.py ]; then
    # Add to get_localized_fields function
    sed -i "s/'name', 'name_fr', 'name_ru',/&, 'name_${LANG_CODE}',/g" app/core/utils/translation_utils.py
    sed -i "s/'description', 'description_fr', 'description_ru',/&, 'description_${LANG_CODE}',/g" app/core/utils/translation_utils.py
    sed -i "s/'title', 'title_fr', 'title_ru',/&, 'title_${LANG_CODE}',/g" app/core/utils/translation_utils.py
    sed -i "s/'subtitle', 'subtitle_fr', 'subtitle_ru'/&, 'subtitle_${LANG_CODE}'/g" app/core/utils/translation_utils.py
    echo "Updated translation_utils.py localized fields"
    
    # Add to get_field_language function
    sed -i "/elif field_name.endswith('_fr'):/a\    elif field_name.endswith('_${LANG_CODE}'):\n        return '${LANG_CODE}'" app/core/utils/translation_utils.py
    echo "Updated get_field_language function"
    
    # Add to get_base_field_name function
    sed -i "s/field_name.endswith(('_ru', '_fr')):/& or field_name.endswith('_${LANG_CODE}')/g" app/core/utils/translation_utils.py
    echo "Updated get_base_field_name function"
    
    # Add to fill_missing_translations priority list
    sed -i "s/\['en', 'fr', 'ru'\]/['en', 'fr', 'ru', '${LANG_CODE}']/g" app/core/utils/translation_utils.py
    echo "Updated fill_missing_translations priority list"
fi

# Update SQL index script
if [ -f scripts/create_index.sql ]; then
    sed -i "/coalesce(title_fr, '')/a\        coalesce(title_${LANG_CODE}, '') || ' ' ||" scripts/create_index.sql
    sed -i "/coalesce(subtitle_fr, '')/a\        coalesce(subtitle_${LANG_CODE}, '') || ' ' ||" scripts/create_index.sql
    sed -i "/coalesce(description_fr, '')/a\        coalesce(description_${LANG_CODE}, '') || ' ' ||" scripts/create_index.sql
    sed -i "/coalesce(recommendation_fr, '')/a\        coalesce(recommendation_${LANG_CODE}, '') || ' ' ||" scripts/create_index.sql
    sed -i "/coalesce(madeof_fr, '')/a\        coalesce(madeof_${LANG_CODE}, '')" scripts/create_index.sql
    echo "Updated create_index.sql"
fi

# Add language schema classes (this requires more complex handling)
if [ -f app/core/schemas/lang_schemas.py ]; then
    # Add new language schema classes at the end of the file
    cat >> app/core/schemas/lang_schemas.py << EOF


class ListView${LANG_NAME}(ListView):
    @computed_field(description='${LANG_NAME} Name',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
        """Возвращает первое непустое значение из name, name_ru, name_fr, name_${LANG_CODE}\"\"\" 
        return self.name_${LANG_CODE} or self.name or self.name_ru or self.name_fr or ""


class DetailView${LANG_NAME}(DetailView):
    @computed_field(description='${LANG_NAME} Name',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_name(self) -> str:
        """Возвращает первое непустое значение из name, name_ru, name_fr, name_${LANG_CODE}\"\"\"
        return self.name_${LANG_CODE} or self.name or self.name_ru or self.name_fr or ""

    @computed_field(description='${LANG_NAME} Description',  # Это будет подписью/лейблом (human readable)
                    title='Отображаемое имя'  # Это для swagger (machine readable)
                    )
    @property
    def display_description(self) -> str:
        return self.description_${LANG_CODE} or self.description or self.description_ru or self.description_fr or ""
EOF
    echo "Added ${LANG_NAME} schema classes to lang_schemas.py"
fi

# Update preact frontend
if [ -f preact_front/src/contexts/LanguageContext.tsx ]; then
    # Update availableLanguages in context initialization
    sed -i "s/availableLanguages: \['en', 'ru', 'fr'\]/availableLanguages: \['en', 'ru', 'fr', '${LANG_CODE}'\]/g" preact_front/src/contexts/LanguageContext.tsx
    sed -i "s/setAvailableLanguages(langs \|\| \['en', 'ru', 'fr'\]);/setAvailableLanguages(langs \|\| \['en', 'ru', 'fr', '${LANG_CODE}'\]);/g" preact_front/src/contexts/LanguageContext.tsx
    sed -i "s/const langs = \['en', 'ru', 'fr'\];/const langs = \['en', 'ru', 'fr', '${LANG_CODE}'\];/g" preact_front/src/contexts/LanguageContext.tsx
    
    # Add new language translations (using English as default)
    sed -i "/  fr: {/r <(echo \"  },\n  ${LANG_CODE}: {\" && grep -A 200 \"  fr: {\" preact_front/src/contexts/LanguageContext.tsx | grep -A 200 \"  }\" | head -n -1)" preact_front/src/contexts/LanguageContext.tsx
    
    # More precise approach for adding language translations
    # First, we need to extract the fr translations and add them as the new language
    echo "Note: Adding language translations to LanguageContext.tsx requires manual update for the ${LANG_CODE} translations section"
fi

# Update translation test
if [ -f tests/qwen/test_translation.py ]; then
    sed -i "s/'name_fr': None,/'name_fr': None,\n        'name_${LANG_CODE}': None,/g" tests/qwen/test_translation.py
    sed -i "s/'description_fr': None,/'description_fr': None,\n        'description_${LANG_CODE}': None,/g" tests/qwen/test_translation.py
    sed -i "s/'title_fr': None,/'title_fr': None,\n        'title_${LANG_CODE}': None,/g" tests/qwen/test_translation.py
    echo "Updated translation test file"
fi

echo "Language $LANG_CODE ($LANG_NAME) has been added to the application!"
echo "Note: You may need to manually update the preact frontend translation section for the new language."