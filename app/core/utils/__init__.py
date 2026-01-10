# app.core.utils.__init__.py
# Avoid circular imports by importing selectively
from .translation_utils import (
    translate_text,
    get_field_language,
    fill_missing_translations,
    get_group_localized_fields)
from .common_utils import localized_field_with_replacement
