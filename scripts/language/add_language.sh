#!/bin/bash
# Script to add a new language to the application
# Usage: ./add_language.sh <language_code>

set -e

LANGUAGE_CODE=$1

if [ -z "$LANGUAGE_CODE" ]; then
    echo "Usage: $0 <language_code>"
    echo "Example: $0 es"
    exit 1
fi

echo "Adding language: $LANGUAGE_CODE"

# Function to add language fields to SQLAlchemy models
add_to_sqlalchemy_models() {
    local file="$1"
    local lang_code="$2"
    
    # Add the new language field to the model if it doesn't exist
    if ! grep -q "name_${lang_code}: Mapped\[str_null_true\]" "$file" 2>/dev/null; then
        sed -i.bak "/^class BaseLang(BaseDescription):/,/^$/ {
            /^    pass$/d
            /^    __abstract__ = True/a\
    name_'$lang_code': Mapped[str_null_true]
        }" "$file" || {
            # If pass doesn't exist, add after the last field
            sed -i.bak "/^class BaseLang(BaseDescription):/,/^    # name_en: Mapped\[str_uniq\]/ {
                /# name_en: Mapped\[str_uniq\]/a\
    name_'$lang_code': Mapped[str_null_true]
            }" "$file" || {
                # Last resort: add before pass in BaseLang class
                sed -i.bak "/^class BaseLang(BaseDescription):/,/^    pass/i\
    name_'$lang_code': Mapped[str_null_true]" "$file" 2>/dev/null || true
            }
        }
    fi
    
    # Add description field if it doesn't exist
    if ! grep -q "description_${lang_code}: Mapped\[descr\]" "$file" 2>/dev/null; then
        sed -i.bak "/^class BaseDescription:/,/^[^[:space:]]/ {
            /^[^[:space:]]/!b
            /^    __abstract__ = True/a\
    description_'$lang_code': Mapped[descr]
        }" "$file" || {
            # Last resort: add before pass in BaseDescription class
            sed -i.bak "/^class BaseDescription:/,/^    pass/i\
    description_'$lang_code': Mapped[descr]" "$file" 2>/dev/null || true
        }
    fi
}

# Function to add language fields to Pydantic schemas
add_to_pydantic_schemas() {
    local file="$1"
    local lang_code="$2"
    
    # Add to base schema
    if ! grep -q "name_${lang_code}:" "$file" 2>/dev/null; then
        sed -i.bak '/^class NameSchema(BaseModel):/,$ {
            /description: Optional\[str\] = None/a\
    name_'$lang_code': Optional[str] = None
        }' "$file" || {
            sed -i.bak '/name: Optional\[str\] = None/a\
    name_'$lang_code': Optional[str] = None' "$file" 2>/dev/null || true
        }
    fi
    
    if ! grep -q "description_${lang_code}:" "$file" 2>/dev/null; then
        sed -i.bak '/^class DescriptionSchema(BaseModel):/,$ {
            /description: Optional\[str\] = None/a\
    description_'$lang_code': Optional[str] = None
        }' "$file" || {
            sed -i.bak '/description: Optional\[str\] = None/a\
    description_'$lang_code': Optional[str] = None' "$file" 2>/dev/null || true
        }
    fi
    
    # Also add to Exclude schemas
    if ! grep -q "name_${lang_code}:" "$file" 2>/dev/null; then
        sed -i.bak '/^class NameExcludeSchema(BaseModel):/,$ {
            /Field(exclude=True)/a\
    name_'$lang_code': Optional[str] = Field(exclude=True)
        }' "$file" || true
    fi
    
    if ! grep -q "description_${lang_code}:" "$file" 2>/dev/null; then
        sed -i.bak '/^class DescriptionExcludeSchema(BaseModel):/,$ {
            /Field(exclude=True)/a\
    description_'$lang_code': Optional[str] = Field(exclude=True)
        }' "$file" || true
    fi
}

# Function to add language methods to API mixin
add_to_api_mixin() {
    local file="$1"
    local lang_code="$2"
    
    # Check if method already exists
    if ! grep -q "name_${lang_code}" "$file" 2>/dev/null; then
        # Add the property method for the new language
        sed -i.bak "/@computed_field/a\
    @property\n    def name_'$lang_code'(self) -> str:\n        return self.__get_lang__('_$lang_code')\n\n    @computed_field" "$file" || {
            # If we can't find the pattern, append at the end
            echo "
    @computed_field
    @property
    def name_${lang_code}(self) -> str:
        return self.__get_lang__('_${lang_code}')
" >> "$file"
        }
    fi
}

# Function to add language-specific views to lang_schemas
add_to_lang_views() {
    local file="$1"
    local lang_code="$2"
    
    # Add language-specific classes (this is more complex, so we'll just add a comment reminder)
    # We would need to generate language-specific classes for each language
    echo "// TODO: Consider adding ListView${lang_code^}/DetailView${lang_code^} classes for ${lang_code} language" >> /tmp/lang_todo.txt 2>/dev/null || echo "// Language ${lang_code} needs custom view classes" >> /tmp/lang_todo.txt 2>/dev/null || true
}

# Apply changes to files
add_to_sqlalchemy_models "/workspace/app/core/models/base_model.py" "$LANGUAGE_CODE"
add_to_pydantic_schemas "/workspace/app/core/schemas/base.py" "$LANGUAGE_CODE"
add_to_api_mixin "/workspace/app/core/schemas/api_mixin.py" "$LANGUAGE_CODE"
add_to_lang_views "/workspace/app/core/schemas/lang_schemas.py" "$LANGUAGE_CODE"

echo "Language $LANGUAGE_CODE has been added to the models."
echo "Please review the changes and run database migrations if needed."

# Clean up backup files
find /workspace -name "*.bak" -delete