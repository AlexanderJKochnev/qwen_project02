#!/usr/bin/env python3
"""
Test script to verify the new translation functionality with rate limit handling
"""

import asyncio
from app.core.utils.translation_utils import translate_text, translation_manager
from app.core.config.project_config import settings


async def test_translation_functionality():
    """Test the new translation functionality"""
    print("Testing translation functionality...")
    
    # Test basic translation
    text = "Hello world"
    print(f"\nOriginal text: {text}")
    
    # Test with MyMemory (should work if properly configured)
    try:
        result = await translate_text(text, source_lang="en", target_lang="ru", test=True)
        print(f"Translation result (with test=True): {result}")
    except Exception as e:
        print(f"Error during translation: {e}")
    
    # Print current service status
    print("\nCurrent service status:")
    for name, service in translation_manager.services.items():
        print(f"- Service: {name}")
        print(f"  Rate limit remaining: {service.rate_limit_remaining}")
        print(f"  Rate limit reset: {service.rate_limit_reset}")
        print(f"  Base URL: {service.base_url}")


if __name__ == "__main__":
    asyncio.run(test_translation_functionality())