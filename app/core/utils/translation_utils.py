import asyncio
import httpx
from typing import Dict, Optional, Any
from app.core.config.project_config import settings


async def translate_text(text: str, source_lang: str = "en", target_lang: str = "ru") -> Optional[str]:
    """
    Translate text using MyMemory translation service

    Args:
        text: Text to translate
        source_lang: Source language code (default: "en")
        target_lang: Target language code (default: "ru")

    Returns:
        Translated text or None if translation failed
    """
    if not text or not text.strip():
        return text

    try:
        params = {
            "q": text,
            "langpair": f"{source_lang}|{target_lang}",
            "de": settings.MYMEMORY_API_EMAIL
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(settings.MYMEMORY_API_BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("responseStatus") == 200 and data.get("responseData"):
                translated_text = data["responseData"]["translatedText"]
                return f"{translated_text} <машинный перевод>"

            return None
    except Exception as e:
        print(f"Translation error: {e}")
        return None


def get_localized_fields() -> list:
    """Get list of localized field names that should be translated"""
    return [
        'name', 'name_fr', 'name_ru',
        'description', 'description_fr', 'description_ru',
        'title', 'title_fr', 'title_ru',
        'subtitle', 'subtitle_fr', 'subtitle_ru'
    ]


def get_field_language(field_name: str) -> Optional[str]:
    """Extract language code from field name"""
    if field_name.endswith('_ru'):
        return 'ru'
    elif field_name.endswith('_fr'):
        return 'fr'
    elif field_name in ['name', 'description', 'title', 'subtitle']:
        return 'en'  # Assuming English is the base language
    return None


def get_base_field_name(field_name: str) -> str:
    """Get the base field name without language suffix"""
    if field_name.endswith(('_ru', '_fr')):
        return field_name[:-3]  # Remove _ru or _fr
    return field_name


# Global variable to hold the current implementation of fill_missing_translations
_fill_missing_translations_impl = None


def set_fill_missing_translations_impl(impl_func):
    """Set the implementation function for fill_missing_translations"""
    global _fill_missing_translations_impl
    _fill_missing_translations_impl = impl_func


def get_fill_missing_translations_impl():
    """Get the current implementation function for fill_missing_translations"""
    global _fill_missing_translations_impl
    if _fill_missing_translations_impl is None:
        # Default implementation
        _fill_missing_translations_impl = _fill_missing_translations_default
    return _fill_missing_translations_impl


async def fill_missing_translations(data: Dict[str, Any]) -> Dict[str, Any]:
    """Wrapper function that delegates to the current implementation"""
    impl = get_fill_missing_translations_impl()
    return await impl(data)


async def _fill_missing_translations_default(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Default implementation: Fill missing translations in data dictionary using available translations

    Args:
        data: Dictionary containing fields that may need translation

    Returns:
        Updated dictionary with filled translations
    """
    if not data:
        return data

    updated_data = data.copy()
    localized_fields = get_localized_fields()

    # Group fields by their base name
    field_groups = {}
    for field_name in localized_fields:
        base_name = get_base_field_name(field_name)
        if base_name not in field_groups:
            field_groups[base_name] = []
        field_groups[base_name].append(field_name)

    # Process each group of related fields
    for base_name, fields in field_groups.items():
        # Check which fields are filled
        filled_fields = {field: data.get(field) for field in fields if data.get(field)}

        # Skip if no source for translation
        if not filled_fields:
            continue

        # Determine source field priority: prefer English, then French, then Russian
        source_field = None
        source_value = None

        # Prefer English as source
        for lang in ['en', 'fr', 'ru']:
            for field_name, value in filled_fields.items():
                if get_field_language(field_name) == lang and value:
                    source_field = field_name
                    source_value = value
                    break
            if source_field:
                break

        if not source_value:
            continue

        # Get source language
        source_lang = get_field_language(source_field)
        if not source_lang:
            continue

        # Fill missing translations
        for field in fields:
            if field not in filled_fields:  # Field is missing
                target_lang = get_field_language(field)
                if target_lang and target_lang != source_lang:
                    # Translate from source to target
                    translated_text = await translate_text(
                        source_value,
                        source_lang=source_lang,
                        target_lang=target_lang
                    )

                    if translated_text:
                        updated_data[field] = translated_text

    return updated_data
