"""Bulk translation utility for all models in the database."""

import asyncio
import sys
import os

# Add the workspace to Python path
sys.path.insert(0, '/workspace')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config.db_config import settings
from .translator import translation_service


async def run_bulk_translation(force_update: bool = False):
    """Run bulk translation for all models in the database."""
    
    # Create database engine and session
    DATABASE_URL = settings.DATABASE_URL
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("Starting bulk translation...")
        
        # Translate all models
        results = await translation_service.translate_all_models(session, force_update)
        
        print("\nTranslation Results:")
        print("=" * 40)
        total_updated = 0
        for model_name, count in results.items():
            print(f"{model_name.capitalize()}: {count} records updated")
            total_updated += count
        
        print("=" * 40)
        print(f"Total records updated: {total_updated}")
        
        await session.commit()


def main():
    """Main function to run the bulk translation."""
    force_update = False
    if len(sys.argv) > 1 and sys.argv[1] == '--force':
        force_update = True
        print("Force update mode enabled - will update existing translations")
    
    asyncio.run(run_bulk_translation(force_update))


if __name__ == "__main__":
    main()