# app.core.utils.__init__.py
# Avoid circular imports by importing selectively
from .translation_utils import (
    translate_text,
    get_field_language,
    get_base_field_name,
    fill_missing_translations
)
