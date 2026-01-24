"""
Meilisearch synchronization service using Transactional Outbox pattern
"""
import asyncio
import json
from typing import List, Optional, Any, Dict
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.models.settings import MeilisearchSettings
from app.core.models.outbox import Outbox
from app.core.config.project_config import settings
from app.support.item.schemas import ItemReadRelation
from app.core.utils.pydantic_key_extractor import extract_keys_with_blacklist


class SearchService:
    def __init__(self):
        self.client = AsyncClient(
            url=settings.MEILISEARCH_URL,
            api_key=settings.MEILISEARCH_MASTER_KEY
        )
        self.index_name = "items"
    
    async def initialize_index(self):
        """Initialize the Meilisearch index with proper settings."""
        try:
            # Get or create the index
            index = self.client.index(self.index_name)
            
            # Configure searchable attributes based on ItemReadRelation schema
            searchable_attrs = extract_keys_with_blacklist(
                ItemReadRelation,
                blacklist=['vol', 'alc', 'price', 'id', 'updated_at', 'created_at', 'count']
            )
            
            # Update index settings
            await index.update_settings(
                MeilisearchSettings(
                    searchable_attributes=searchable_attrs,
                    filterable_attributes=["id"],
                    sortable_attributes=["id"]
                )
            )
            
            logger.info(f"Index '{self.index_name}' configured with searchable attributes: {searchable_attrs}")
        except Exception as e:
            logger.error(f"Failed to initialize index: {e}")
            raise
    
    async def sync_outbox(self, session: AsyncSession, batch_size: int = 100):
        """Process unprocessed outbox entries and sync with Meilisearch."""
        try:
            # Get unprocessed entries
            stmt = select(Outbox).where(
                and_(Outbox.entity_type == 'item', Outbox.processed == False)
            ).limit(batch_size)
            
            result = await session.execute(stmt)
            entries = result.scalars().all()
            
            if not entries:
                logger.info("No pending outbox entries to process")
                return
            
            logger.info(f"Processing {len(entries)} outbox entries")
            
            for entry in entries:
                try:
                    payload = json.loads(entry.payload) if entry.payload else {}
                    
                    if entry.operation == 'DELETE':
                        await self._handle_delete(entry.entity_id)
                    else:
                        await self._handle_upsert(payload, entry.operation)
                    
                    # Mark as processed
                    update_stmt = update(Outbox).where(Outbox.id == entry.id).values(
                        processed=True,
                        processed_at=datetime.utcnow()
                    )
                    await session.execute(update_stmt)
                    await session.commit()
                    
                    logger.info(f"Successfully processed outbox entry {entry.id}")
                    
                except Exception as e:
                    # Log error and mark as failed
                    update_stmt = update(Outbox).where(Outbox.id == entry.id).values(
                        processed=True,
                        processed_at=datetime.utcnow(),
                        error_message=str(e)
                    )
                    await session.execute(update_stmt)
                    await session.commit()
                    
                    logger.error(f"Failed to process outbox entry {entry.id}: {e}")
        
        except Exception as e:
            logger.error(f"Error processing outbox: {e}")
            raise
    
    async def _handle_upsert(self, document: Dict[str, Any], operation: str):
        """Handle upsert operation in Meilisearch."""
        try:
            index = self.client.index(self.index_name)
            
            # Add document to Meilisearch
            task_info = await index.add_documents([document])
            
            # Wait for the task to complete
            await self.client.wait_for_task(task_info.task_uid)
            
            logger.info(f"Document {document.get('id', 'unknown')} {operation.lower()}ed successfully")
        except Exception as e:
            logger.error(f"Failed to {operation.lower()} document: {e}")
            raise
    
    async def _handle_delete(self, entity_id: int):
        """Handle delete operation in Meilisearch."""
        try:
            index = self.client.index(self.index_name)
            
            # Delete document from Meilisearch
            task_info = await index.delete_document(str(entity_id))
            
            # Wait for the task to complete
            await self.client.wait_for_task(task_info.task_uid)
            
            logger.info(f"Document {entity_id} deleted successfully")
        except Exception as e:
            logger.error(f"Failed to delete document {entity_id}: {e}")
            raise
    
    async def search(self, query: str, page: int = 1, page_size: int = 20, lang: str = 'en'):
        """Perform search in Meilisearch."""
        try:
            index = self.client.index(self.index_name)
            
            search_results = await index.search(
                query,
                offset=(page - 1) * page_size,
                limit=page_size,
                show_matches_position=True
            )
            
            return {
                'results': search_results.hits,
                'total': search_results.estimated_total_hits,
                'page': page,
                'page_size': page_size,
                'total_pages': (search_results.estimated_total_hits + page_size - 1) // page_size
            }
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def close(self):
        """Close the Meilisearch client."""
        await self.client.aclose()


# Global search service instance
search_service = SearchService()