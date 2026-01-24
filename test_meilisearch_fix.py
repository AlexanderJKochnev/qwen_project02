#!/usr/bin/env python3
"""
Test script to verify that the Meilisearch search method fix works properly
"""
from unittest.mock import AsyncMock, MagicMock, patch
from meilisearch_python_sdk import AsyncClient
from app.core.services.search_service import SearchService


async def test_search_method_call_format():
    """
    Test that the search method is called with correct arguments format
    """
    # Create a search result mock
    mock_search_result = MagicMock()
    mock_search_result.hits = [{"id": 1, "title": "Test"}]
    mock_search_result.estimated_total_hits = 1
    
    # Mock the entire client initialization and search process
    with patch('app.core.services.search_service.AsyncClient') as mock_async_client_class:
        # Create mock instances
        mock_client_instance = AsyncMock()
        mock_index_instance = AsyncMock()
        
        # Setup the mock chain
        mock_async_client_class.return_value = mock_client_instance
        mock_client_instance.index.return_value = mock_index_instance
        mock_index_instance.search = AsyncMock(return_value=mock_search_result)
        
        # Create the service instance (this will use the mocked client)
        service = SearchService()
        
        # Call the search method
        try:
            result = await service.search("test query", page=1, page_size=10)
            
            # Verify that search was called with correct arguments
            mock_index_instance.search.assert_called_once_with(
                "test query",
                offset=0,  # (page-1)*page_size = (1-1)*10 = 0
                limit=10,  # page_size
                show_matches_position=True
            )
            
            print("✅ SUCCESS: Search method called with correct argument format!")
            print(f"✅ Result: {result}")
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(test_search_method_call_format())
    if success:
        print("\n🎉 All tests passed! The Meilisearch integration fix is working correctly.")
    else:
        print("\n💥 Tests failed!")
        exit(1)