"""
Background task handler for synchronizing outbox entries with Meilisearch
"""
import asyncio
import json
from typing import Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from meilisearch_python_sdk import AsyncClient

from app.core.config.database.db_async import get_db
from app.core.config.database.meili_async import get_meili_client
from app.core.models.outbox import Outbox
from app.core.services.meili_service import ItemMeiliService
from app.support.item.model import Item
from app.support.item.schemas import ItemReadRelation
from loguru import logger


class MeiliSearchSyncWorker:
    """
    Background worker to process outbox entries and synchronize with Meilisearch
    """
    
    def __init__(self):
        self.running = False
        self.item_service = ItemMeiliService()
    
    async def process_outbox_entries(self):
        """
        Process unprocessed outbox entries and synchronize with Meilisearch
        """
        try:
            # Get database session
            async for db_session in get_db():
                # Get unprocessed entries
                unprocessed_query = Outbox.get_unprocessed_entries(entity_type='item', limit=100)
                result = await db_session.execute(unprocessed_query)
                unprocessed_entries = result.scalars().all()
                
                if not unprocessed_entries:
                    continue
                
                # Process each entry
                processed_entries = []
                failed_entries = []
                
                # Get Meilisearch client
                async with get_meili_client() as client:
                    for entry in unprocessed_entries:
                        try:
                            success = await self._process_single_entry(entry, client, db_session)
                            if success:
                                processed_entries.append(entry.id)
                            else:
                                failed_entries.append(entry.id)
                        except Exception as e:
                            logger.error(f"Failed to process outbox entry {entry.id}: {str(e)}")
                            failed_entries.append(entry.id)
                
                # Mark processed entries
                if processed_entries:
                    stmt = Outbox.mark_as_processed(processed_entries)
                    await db_session.execute(stmt)
                
                # Mark failed entries
                for failed_id in failed_entries:
                    stmt = Outbox.mark_as_failed(failed_id, "Processing failed")
                    await db_session.execute(stmt)
                
                await db_session.commit()
                
                # If we processed entries, continue immediately, otherwise wait
                if processed_entries or failed_entries:
                    continue  # Continue to next batch immediately
                else:
                    break  # No more entries to process
        
        except Exception as e:
            logger.error(f"Error in MeiliSearchSyncWorker.process_outbox_entries: {str(e)}")
    
    async def _process_single_entry(self, entry: Outbox, client: AsyncClient, db_session: AsyncSession) -> bool:
        """
        Process a single outbox entry
        """
        try:
            if entry.operation == 'INSERT':
                await self._handle_insert(entry, client, db_session)
            elif entry.operation == 'UPDATE':
                await self._handle_update(entry, client, db_session)
            elif entry.operation == 'DELETE':
                await self._handle_delete(entry, client)
            else:
                logger.warning(f"Unknown operation type: {entry.operation}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error processing entry {entry.id}: {str(e)}")
            return False
    
    async def _handle_insert(self, entry: Outbox, client: AsyncClient, db_session: AsyncSession):
        """
        Handle INSERT operation - add document to Meilisearch
        """
        # Get the item from database to ensure we have fresh data
        item_query = await db_session.get(Item, entry.entity_id)
        if item:
            # Validate through Pydantic schema to ensure consistency
            validated_item = ItemReadRelation.model_validate(item)
            document = validated_item.model_dump(mode='json')
            
            # Add document to Meilisearch
            index = client.index(self.item_service.index_name)
            await index.add_documents([document])
            logger.info(f"Added document {entry.entity_id} to Meilisearch")
        else:
            logger.warning(f"Item with ID {entry.entity_id} not found in database for INSERT operation")
    
    async def _handle_update(self, entry: Outbox, client: AsyncClient, db_session: AsyncSession):
        """
        Handle UPDATE operation - update document in Meilisearch
        """
        # Get the item from database to ensure we have fresh data
        item_query = await db_session.get(Item, entry.entity_id)
        if item:
            # Validate through Pydantic schema to ensure consistency
            validated_item = ItemReadRelation.model_validate(item)
            document = validated_item.model_dump(mode='json')
            
            # Update document in Meilisearch
            index = client.index(self.item_service.index_name)
            await index.add_documents([document])  # Meilisearch upserts on add
            logger.info(f"Updated document {entry.entity_id} in Meilisearch")
        else:
            logger.warning(f"Item with ID {entry.entity_id} not found in database for UPDATE operation")
    
    async def _handle_delete(self, entry: Outbox, client: AsyncClient):
        """
        Handle DELETE operation - remove document from Meilisearch
        """
        # Remove document from Meilisearch
        index = client.index(self.item_service.index_name)
        await index.delete_document(str(entry.entity_id))
        logger.info(f"Deleted document {entry.entity_id} from Meilisearch")
    
    async def start_worker(self):
        """
        Start the background synchronization worker
        """
        self.running = True
        logger.info("Starting MeiliSearch Sync Worker...")
        
        while self.running:
            try:
                await self.process_outbox_entries()
                # Wait 5 seconds before next processing cycle
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Error in sync worker loop: {str(e)}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def stop_worker(self):
        """
        Stop the background synchronization worker
        """
        self.running = False
        logger.info("Stopping MeiliSearch Sync Worker...")


# Global instance for use in main application
meili_sync_worker = MeiliSearchSyncWorker()