#!/bin/bash
# Script to add new language support to the application
# Usage: ./add_language_fixed.sh <lang_code> <lang_name>
# Example: ./add_language_fixed.sh es Spanish

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
    # Update BaseDescription class
    sed -i "/description_fr: Mapped\[descr\]/a\    description_${LANG_CODE}: Mapped[descr]" app/core/models/base_model.py
    echo "Updated BaseDescription in base_model.py"
    
    # Update BaseLang class
    sed -i "/name_fr: Mapped\[str_null_true\]/a\    name_${LANG_CODE}: Mapped[str_null_true]" app/core/models/base_model.py
    echo "Updated BaseLang in base_model.py"
fi

# Update drink model - Lang class
if [ -f app/support/drink/model.py ]; then
    # Add fields to Lang class
    sed -i "/title_fr: Mapped\[str_null_true\]/a\    title_${LANG_CODE}: Mapped[str_null_true]" app/support/drink/model.py
    sed -i "/subtitle_fr: Mapped\[str_null_true\]/a\    subtitle_${LANG_CODE}: Mapped[str_null_true]" app/support/drink/model.py
    sed -i "/description_fr: Mapped\[descr\]/a\    description_${LANG_CODE}: Mapped[descr]" app/support/drink/model.py
    sed -i "/recommendation_fr: Mapped\[descr\]/a\    recommendation_${LANG_CODE}: Mapped[descr]" app/support/drink/model.py
    sed -i "/madeof_fr: Mapped\[descr\]/a\    madeof_${LANG_CODE}: Mapped[descr]" app/support/drink/model.py
    echo "Updated Lang class in drink model"
    
    # Update SQL index in the model (inside create_gin_index_sql)
    sed -i "/coalesce(title_fr, '')/a\             coalesce(title_${LANG_CODE}, '') || ' ' ||" app/support/drink/model.py
    sed -i "/coalesce(subtitle_fr, '')/a\             coalesce(subtitle_${LANG_CODE}, '') || ' ' ||" app/support/drink/model.py
    sed -i "/coalesce(description_fr, '')/a\             coalesce(description_${LANG_CODE}, '') || ' ' ||" app/support/drink/model.py
    sed -i "/coalesce(recommendation_fr, '')/a\             coalesce(recommendation_${LANG_CODE}, '') || ' ' ||" app/support/drink/model.py
    sed -i "/coalesce(madeof_fr, ''))/a\             coalesce(madeof_${LANG_CODE}, ''))" app/support/drink/model.py
    echo "Updated SQL index in drink model"
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

# Add language schema classes
if [ -f app/core/schemas/lang_schemas.py ]; then
    # Add new language schema classes at the end of the file before the last line
    sed -i "/^$/d" app/core/schemas/lang_schemas.py  # Remove any trailing empty lines
    # Add ListView and DetailView for the new language
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

# Update preact frontend - LanguageContext.tsx
if [ -f preact_front/src/contexts/LanguageContext.tsx ]; then
    # Update availableLanguages initialization
    sed -i "s/availableLanguages: \['en', 'ru', 'fr'\]/availableLanguages: \['en', 'ru', 'fr', '${LANG_CODE}'\]/g" preact_front/src/contexts/LanguageContext.tsx
    
    # Update fallback languages in the useEffect
    sed -i "s/const langs = \['en', 'ru', 'fr'\];/const langs = \['en', 'ru', 'fr', '${LANG_CODE}'\];/g" preact_front/src/contexts/LanguageContext.tsx
    
    # Add a new language section to the translations object
    # First, find the end of the 'fr' section and add the new language after it
    sed -i "/  },$/ {
        /  fr: {/,/  },$/ {
            /  },$/ {
                r /dev/stdin
            }
        }
    }" preact_front/src/contexts/LanguageContext.tsx << EOF
  ${LANG_CODE}: {
    welcome: '${LANG_NAME} Welcome',
    language: '${LANG_NAME} Language',
    home: '${LANG_NAME} Home',
    about: '${LANG_NAME} About',
    contact: '${LANG_NAME} Contact',
    login: '${LANG_NAME} Login',
    logout: '${LANG_NAME} Logout',
    username: '${LANG_NAME} Username',
    password: '${LANG_NAME} Password',
    submit: '${LANG_NAME} Submit',
    cancel: '${LANG_NAME} Cancel',
    save: '${LANG_NAME} Save',
    edit: '${LANG_NAME} Edit',
    delete: '${LANG_NAME} Delete',
    search: '${LANG_NAME} Search',
    filter: '${LANG_NAME} Filter',
    create: '${LANG_NAME} Create',
    update: '${LANG_NAME} Update',
    view: '${LANG_NAME} View',
    details: '${LANG_NAME} Details',
    items: '${LANG_NAME} Items',
    item: '${LANG_NAME} Item',
    name: '${LANG_NAME} Name',
    description: '${LANG_NAME} Description',
    actions: '${LANG_NAME} Actions',
    confirm: '${LANG_NAME} Confirm',
    confirmDelete: '${LANG_NAME} Are you sure you want to delete this item?',
    yes: '${LANG_NAME} Yes',
    no: '${LANG_NAME} No',
    success: '${LANG_NAME} Success',
    error: '${LANG_NAME} Error',
    loading: '${LANG_NAME} Loading...',
    noData: '${LANG_NAME} No data available',
    back: '${LANG_NAME} Back',
    next: '${LANG_NAME} Next',
    previous: '${LANG_NAME} Previous',
    first: '${LANG_NAME} First',
    last: '${LANG_NAME} Last',
    of: '${LANG_NAME} of',
    results: '${LANG_NAME} results',
    total: '${LANG_NAME} Total',
    page: '${LANG_NAME} Page',
    records: '${LANG_NAME} records',
    settings: '${LANG_NAME} Settings',
    profile: '${LANG_NAME} Profile',
    dashboard: '${LANG_NAME} Dashboard',
    admin: '${LANG_NAME} Admin',
    user: '${LANG_NAME} User',
    role: '${LANG_NAME} Role',
    status: '${LANG_NAME} Status',
    active: '${LANG_NAME} Active',
    inactive: '${LANG_NAME} Inactive',
    enabled: '${LANG_NAME} Enabled',
    disabled: '${LANG_NAME} Disabled',
    date: '${LANG_NAME} Date',
    time: '${LANG_NAME} Time',
    created: '${LANG_NAME} Created',
    updated: '${LANG_NAME} Updated',
    deleted: '${LANG_NAME} Deleted',
    refresh: '${LANG_NAME} Refresh',
    download: '${LANG_NAME} Download',
    upload: '${LANG_NAME} Upload',
    import: '${LANG_NAME} Import',
    export: '${LANG_NAME} Export',
    print: '${LANG_NAME} Print',
    share: '${LANG_NAME} Share',
    copy: '${LANG_NAME} Copy',
    paste: '${LANG_NAME} Paste',
    cut: '${LANG_NAME} Cut',
    select: '${LANG_NAME} Select',
    all: '${LANG_NAME} All',
    none: '${LANG_NAME} None',
    clear: '${LANG_NAME} Clear',
    reset: '${LANG_NAME} Reset',
    apply: '${LANG_NAME} Apply',
    close: '${LANG_NAME} Close',
    open: '${LANG_NAME} Open',
    minimize: '${LANG_NAME} Minimize',
    maximize: '${LANG_NAME} Maximize',
    restore: '${LANG_NAME} Restore',
    help: '${LANG_NAME} Help',
    aboutApp: '${LANG_NAME} About Application',
    version: '${LANG_NAME} Version',
    copyright: '${LANG_NAME} Copyright',
    privacy: '${LANG_NAME} Privacy Policy',
    terms: '${LANG_NAME} Terms of Service',
    cookies: '${LANG_NAME} Cookies',
    accessibility: '${LANG_NAME} Accessibility',
    feedback: '${LANG_NAME} Feedback',
    support: '${LANG_NAME} Support',
    documentation: '${LANG_NAME} Documentation',
    tutorial: '${LANG_NAME} Tutorial',
    examples: '${LANG_NAME} Examples',
    faq: '${LANG_NAME} FAQ',
    news: '${LANG_NAME} News',
    updates: '${LANG_NAME} Updates',
    notifications: '${LANG_NAME} Notifications',
    messages: '${LANG_NAME} Messages',
    inbox: '${LANG_NAME} Inbox',
    sent: '${LANG_NAME} Sent',
    drafts: '${LANG_NAME} Drafts',
    spam: '${LANG_NAME} Spam',
    trash: '${LANG_NAME} Trash',
    calendar: '${LANG_NAME} Calendar',
    events: '${LANG_NAME} Events',
    tasks: '${LANG_NAME} Tasks',
    reminders: '${LANG_NAME} Reminders',
    notes: '${LANG_NAME} Notes',
    files: '${LANG_NAME} Files',
    folders: '${LANG_NAME} Folders',
    tags: '${LANG_NAME} Tags',
    categories: '${LANG_NAME} Categories',
    filters: '${LANG_NAME} Filters',
    sorting: '${LANG_NAME} Sorting',
    group: '${LANG_NAME} Group',
    order: '${LANG_NAME} Order',
    ascending: '${LANG_NAME} Ascending',
    descending: '${LANG_NAME} Descending',
    equal: '${LANG_NAME} Equal',
    notEqual: '${LANG_NAME} Not Equal',
    greater: '${LANG_NAME} Greater',
    less: '${LANG_NAME} Less',
    greaterOrEqual: '${LANG_NAME} Greater or Equal',
    lessOrEqual: '${LANG_NAME} Less or Equal',
    contains: '${LANG_NAME} Contains',
    startsWith: '${LANG_NAME} Starts With',
    endsWith: '${LANG_NAME} Ends With',
    empty: '${LANG_NAME} Empty',
    notEmpty: '${LANG_NAME} Not Empty',
    null: '${LANG_NAME} Null',
    notNull: '${LANG_NAME} Not Null',
    today: '${LANG_NAME} Today',
    yesterday: '${LANG_NAME} Yesterday',
    tomorrow: '${LANG_NAME} Tomorrow',
    thisWeek: '${LANG_NAME} This Week',
    lastWeek: '${LANG_NAME} Last Week',
    nextWeek: '${LANG_NAME} Next Week',
    thisMonth: '${LANG_NAME} This Month',
    lastMonth: '${LANG_NAME} Last Month',
    nextMonth: '${LANG_NAME} Next Month',
    thisYear: '${LANG_NAME} This Year',
    lastYear: '${LANG_NAME} Last Year',
    nextYear: '${LANG_NAME} Next Year',
  },
EOF
    echo "Updated LanguageContext.tsx with ${LANG_CODE} language section"
fi

# Update translation test
if [ -f tests/qwen/test_translation.py ]; then
    sed -i "/'name_fr': None,/a\        'name_${LANG_CODE}': None," tests/qwen/test_translation.py
    sed -i "/'description_fr': None,/a\        'description_${LANG_CODE}': None," tests/qwen/test_translation.py
    sed -i "/'title_fr': None,/a\        'title_${LANG_CODE}': None," tests/qwen/test_translation.py
    echo "Updated translation test file"
fi

echo "Language $LANG_CODE ($LANG_NAME) has been added to the application!"
echo "Note: You may need to adjust the placeholder translations in the frontend for the new language."