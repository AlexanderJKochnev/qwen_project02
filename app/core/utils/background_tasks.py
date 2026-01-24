# app/core/utils/bacground_tasks.py

"""
Background tasks for processing Meilisearch outbox
"""
import asyncio
# from typing import Callable
from loguru import logger
# from sqlalchemy.ext.asyncio import AsyncSession
from app.core.services.search_service import search_service
from app.core.config.database.db_async import get_db


async def process_meilisearch_outbox():
    """
    Background task to process Meilisearch outbox entries
    This function runs continuously to sync changes with Meilisearch
    """
    while True:
        try:
            # Get a database session
            async for session in get_db():
                # Process outbox entries
                await search_service.sync_outbox(session, batch_size=100)
                break  # Exit the loop after processing once per iteration

            # Wait before next processing cycle
            await asyncio.sleep(5)  # Process every 5 seconds

        except Exception as e:
            logger.error(f"Error in Meilisearch outbox processor: {e}")
            await asyncio.sleep(10)  # Wait longer on error


async def start_background_tasks():
    """
    Start all background tasks as asyncio tasks
    """
    # Initialize the search index
    try:
        await search_service.initialize_index()
        logger.info("Meilisearch index initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Meilisearch index: {e}")

    # Start the outbox processor as a background task
    outbox_processor_task = asyncio.create_task(process_meilisearch_outbox())
    logger.info("Started Meilisearch outbox processor background task")
    return [outbox_processor_task]
    

# Global variable to hold background tasks
background_tasks = []


async def init_background_tasks():
    """
    Initialize and start all background tasks
    """
    global background_tasks
    background_tasks = await start_background_tasks()


async def stop_background_tasks():
    """
    Stop all background tasks gracefully
    """
    global background_tasks
    for task in background_tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    logger.info("Stopped all background tasks")
