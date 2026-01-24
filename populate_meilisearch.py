#!/usr/bin/env python3
"""
Macro script to manually populate the Meilisearch index with existing data.
This script can be run manually to initially fill the Meilisearch index with all existing items.
"""

import asyncio
import sys
import os

# Add the workspace to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.services.search_service import search_service


async def main():
    """Main function to populate Meilisearch index."""
    print("Starting Meilisearch index population...")
    
    try:
        # Initialize the search index first
        print("Initializing Meilisearch index...")
        await search_service.initialize_index()
        print("Meilisearch index initialized successfully.")
        
        # Populate the index with existing data
        print("Populating Meilisearch index with existing data...")
        await search_service.populate_index_from_db(batch_size=100)
        print("Meilisearch index populated successfully!")
        
    except Exception as e:
        print(f"Error occurred during Meilisearch index population: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Close the search service
        await search_service.close()


if __name__ == "__main__":
    asyncio.run(main())