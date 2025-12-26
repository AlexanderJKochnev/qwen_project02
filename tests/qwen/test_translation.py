#!/usr/bin/env python3
"""
Test script for MyMemory translation functionality
"""

import asyncio
from app.core.utils.translation_utils import translate_text, fill_missing_translations


async def test_translation():
    print("Testing translation functionality...")
    
    # Test basic translation
    text = "Wine with syrupy blackberry and blue-berry aromas"
    translated = await translate_text(text, source_lang="en", target_lang="ru")
    print(f"Original: {text}")
    print(f"Translated: {translated}")
    print()
    
    # Test filling missing translations
    test_data = {
        'name': 'Eagle',
        'name_fr': None,
        'name_cn': None,
        'name_es': None,
        'name_ru': None,
        'description': 'A beautiful bird',
        'description_fr': None,
        'description_cn': None,
        'description_es': None,
        'description_ru': 'Прекрасная птица',
        'title': 'Golden Eagle',
        'title_fr': None,
        'title_cn': None,
        'title_es': None,
        'title_ru': None,
        'other_field': 'Some other value'
    }
    
    print("Original data:", test_data)
    translated_data = await fill_missing_translations(test_data)
    print("After translation:", translated_data)


if __name__ == "__main__":
    asyncio.run(test_translation())