# app/core/utils/translation_utils.py
import asyncio  # noqa: F401
import httpx
from typing import Dict, Optional, Any, List
from app.core.config.project_config import settings


async def translate_text(text: str, source_lang: str = "en",
                         target_lang: str = "ru",
                         mark: str = "ai",
                         test: bool = False) -> Optional[str]:
    """
    Translate text using MyMemory translation service

    Args:
        text: Text to translate
        source_lang: Source language code (default: "en")
        target_lang: Target language code (default: "ru")
        mark:  отметка о машинном переводе
        test: used for test purpose only
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
        if test:
            print(f"translate_text.{params=}")
            return f"{text} <{mark}>"
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.MYMEMORY_API_BASE_URL, params=params)
            response.raise_for_status()

            data = response.json()

            if data.get("responseStatus") == 200 and data.get("responseData"):
                translated_text = data["responseData"]["translatedText"]
                return f"{translated_text} <{mark}>"

            return None
    except Exception as e:
        print(f"Translation error: {e}")
        return None


def get_group_localized_fields(langs: list, default_lang: str, localized_fields: list) -> Dict[str, List[str]]:
    """Get dict of localized field names that should be translated"""
    languages = [f'_{lang}' if lang != default_lang else '' for lang in langs]
    result: dict = {}
    for field in localized_fields:
        result[field] = [f'{field}{lang}' for lang in languages]
    return result


def localized_field_with_replacement(source: Dict[str, Any], key: str,
                                     langs: list, target_key: str = None) -> Dict[str, Any]:
    """
        1. Извлекает из словаря source значения key на всех языках
        2. Выбирает первое не пустое (langs - список suffixes языков отсортированных по приоритету)
        3. Возвращает словарь из одной пары target_key: val
    """
    for lang in langs:
        res = source.get(f'{key}{lang}')
        if res:
            return {target_key or key: res}
    else:
        return {target_key or key: None}


def get_localized_fields() -> list:
    """Get list of localized field names that should be translated
        DELETE !!
    """
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    langs = [f'_{lang}'if lang != default_lang else '' for lang in settings.LANGUAGES]
    localized_fields = settings.FIELDS_LOCALIZED
    return [f'{field}{lang}' for field in localized_fields for lang in langs]


def get_field_language(field_name: str) -> Optional[str]:
    """Extract language code from field name"""
    if len(field_name) < 3 or field_name[-3] != '_':
        return settings.DEFAULT_LANG
    lang_code = field_name[-2:]
    # Check if the extracted code is in the configured languages
    if lang_code in settings.LANGUAGES:
        return lang_code
    return settings.DEFAULT_LANG


def get_base_field_name(field_name: str) -> str:
    """Get the base field name without language suffix
        DELETE !!!
    """
    # Check for any language suffix from the configured languages
    for lang in sorted(settings.LANGUAGES, key=len, reverse=True):  # Sort by length descending to match longer suffixes first
        if lang != settings.DEFAULT_LANG and field_name.endswith(f'_{lang}'):
            return field_name[:-len(lang)-1]  # Remove _lang suffix
    return field_name


async def fill_missing_translations(data: Dict[str, Any], test: bool = False) -> Dict[str, Any]:
    """
    Fill missing translations in data dictionary using available translations

    Args:
        data: Dictionary containing fields that may need translation

    Returns:
        Updated dictionary with filled translations
    """
    if not data:
        return data

    updated_data = data.copy()

    # language
    langs = settings.LANGUAGES
    default_lang = settings.DEFAULT_LANG
    localized_fields = settings.FIELDS_LOCALIZED
    mark = settings.MACHINE_TRANSLATION_MARK
    # Group fields by their base name {'name': ['name', 'name_ru', 'name_fr', ...], ...}
    field_groups = get_group_localized_fields(langs, default_lang, localized_fields)

    # Process each group of related fields
    for base_name, fields in field_groups.items():
        # Check which fields are filled
        # {'name': 'text', 'name_ru': 'текст', ...}
        filled_fields = {field: data.get(field) for field in fields if data.get(field)}

        # Skip if no source for translation
        if not filled_fields:
            continue

        # Determine source field priority: prefer First in language, then Second, then Next
        source_field = None
        source_value = None

        # Find source -- first non empty fields
        for lang in langs:
            for field_name, value in filled_fields.items():
                if get_field_language(field_name) == lang and value:
                    source_field = field_name
                    source_value = value
                    source_lang = lang
                    break
            if source_field:
                break

        if not source_value:    # no source found
            continue            # skip translation

        # Fill missing translations
        for field in fields:
            if field not in filled_fields:  # Field is missing
                target_lang = get_field_language(field)
                if target_lang and target_lang != source_lang:
                    # Translate from source to target
                    translated_text = await translate_text(
                        source_value,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        mark=mark,
                        test=test
                    )

                    if translated_text:
                        updated_data[field] = translated_text

    return updated_data


async def fill_missing_translations_old(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fill missing translations in data dictionary using available translations

    Args:
        data: Dictionary containing fields that may need translation

    Returns:
        Updated dictionary with filled translations
        DELETE !!!
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

        # Prefer languages according to the configured order
        for lang in settings.LANGUAGES:
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
