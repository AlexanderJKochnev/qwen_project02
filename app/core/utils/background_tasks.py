# app/core/utils/background_tasks.py

"""
Background tasks for processing Meilisearch outbox
"""
import asyncio
# from typing import Callable
from loguru import logger
# from sqlalchemy.ext.asyncio import AsyncSession
from app.core.utils.search_sync import meili_sync_worker
from app.core.config.database.db_async import get_db

async def process_meilisearch_outbox():
    """
    Background task to process Meilisearch outbox entries
    This function runs continuously to sync changes with Meilisearch
    """
    # Start the MeiliSearch synchronization worker
    await meili_sync_worker.start_worker()


async def start_background_tasks(populate_initial_data: bool = False):
    """
    Start all background tasks as asyncio tasks
    """
    # Start the outbox processor as a background task
    outbox_processor_task = asyncio.create_task(process_meilisearch_outbox())
    logger.info("Started Meilisearch outbox processor background task")
    return [outbox_processor_task]


# Global variable to hold background tasks
background_tasks = []


async def init_background_tasks(populate_initial_data: bool = False):
    """
    Initialize and start all background tasks
    """
    global background_tasks
    background_tasks = await start_background_tasks(populate_initial_data=populate_initial_data)


async def stop_background_tasks():
    """
    Stop all background tasks gracefully
    """
    global background_tasks
    # Stop the MeiliSearch synchronization worker
    await meili_sync_worker.stop_worker()
    logger.info("Stopped all background tasks")
