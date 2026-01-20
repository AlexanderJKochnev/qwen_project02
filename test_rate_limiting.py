#!/usr/bin/env python3
"""
Test script to verify the rate limiting functionality of the translation services
"""

import asyncio
from app.core.utils.translation_utils import (
    MyMemoryTranslationService, 
    GrokCloudTranslationService, 
    TranslationManager,
    translate_text
)
from app.core.config.project_config import settings


def test_header_parsing():
    """Test the rate limit header parsing functionality"""
    print("Testing rate limit header parsing...")
    
    from app.core.utils.translation_utils import TranslationService
    
    # Create a mock service instance
    service = TranslationService("test", "http://example.com")
    
    # Test various header formats
    headers_tests = [
        # Test case 1: ratelimit-remaining-tokens
        ({
            'ratelimit-remaining-tokens': '100',
            'ratelimit-reset': '123456'
        }, 100, 123456),
        
        # Test case 2: x-ratelimit-remaining
        ({
            'x-ratelimit-remaining': '50',
            'x-ratelimit-reset': '789012'
        }, 50, 789012),
        
        # Test case 3: retry-after
        ({
            'retry-after': '60'  # Should be added to current time
        }, 0, 0),  # Will depend on current time
        
        # Test case 4: mixed headers
        ({
            'ratelimit-remaining-tokens': '75',
            'x-ratelimit-remaining': '50',  # This should overwrite the first
            'retry-after': '30'
        }, 50, 0),  # Will depend on current time
    ]
    
    import time
    for i, (headers, expected_remaining, expected_reset) in enumerate(headers_tests):
        service.rate_limit_remaining = float('inf')
        service.rate_limit_reset = 0
        
        print(f"\nTest case {i+1}: {headers}")
        service.update_rate_limits(headers)
        
        print(f"  After parsing - Remaining: {service.rate_limit_remaining}, Reset: {service.rate_limit_reset}")
        
        if expected_remaining != 0:  # We skip checking for retry-after cases as they involve current time
            if service.rate_limit_remaining != expected_remaining:
                print(f"  WARNING: Expected remaining {expected_remaining}, got {service.rate_limit_remaining}")
            else:
                print(f"  ✓ Remaining tokens correctly parsed")


async def test_service_selection():
    """Test service selection logic based on rate limits"""
    print("\nTesting service selection logic...")
    
    manager = TranslationManager()
    
    # Simulate rate limit scenarios
    print(f"Available services: {list(manager.services.keys())}")
    
    # Test when MyMemory has unlimited quota
    mymemory_service = manager.services.get('mymemory')
    if mymemory_service:
        mymemory_service.rate_limit_remaining = 10
        mymemory_service.rate_limit_reset = 0
        print(f"MyMemory rate limit: {mymemory_service.rate_limit_remaining}")
    
    grokcloud_service = manager.services.get('grokcloud')
    if grokcloud_service:
        grokcloud_service.rate_limit_remaining = 5
        grokcloud_service.rate_limit_reset = 0
        print(f"GrokCloud rate limit: {grokcloud_service.rate_limit_remaining}")
    
    # Test the service selection logic
    available_services = []
    for name, service in manager.services.items():
        if service.rate_limit_remaining > 0 or service.rate_limit_remaining == float('inf'):
            if service.rate_limit_reset <= 0:  # Assuming no reset needed
                available_services.append((name, service))
    
    print(f"Available services for use: {[name for name, service in available_services]}")


async def main():
    """Main test function"""
    print("Testing rate limiting functionality...\n")
    
    test_header_parsing()
    await test_service_selection()
    
    print("\nRate limiting tests completed!")


if __name__ == "__main__":
    asyncio.run(main())