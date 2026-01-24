"""
Search hooks to handle indexing when items are created/updated/deleted
"""
from typing import Optional
from datetime import datetime
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.utils.item_search_service import item_search_service
from app.support.item.model import Item


async def index_item_after_creation(db: AsyncSession, item: Item):
    """
    Hook to index item after creation
    """
    try:
        # Create ItemReadRelation object for indexing
        from app.support.item.schemas import ItemReadRelation
        
        item_read = ItemReadRelation(
            id=item.id,
            drink=item.drink,
            vol=item.vol,
            price=item.price,
            count=item.count,
            image_path=item.image_path,
            image_id=item.image_id
        )
        
        # Convert to dict for indexing
        doc_dict = item_read.model_dump(mode='python')
        
        # Index in Meilisearch
        await item_search_service.index_document(item_search_service.index_name, doc_dict)
        
        logger.info(f"Item {item.id} indexed successfully after creation")
    except Exception as e:
        logger.error(f"Error indexing item {item.id} after creation: {e}")


async def index_item_after_update(db: AsyncSession, item: Item):
    """
    Hook to update item index after update
    """
    try:
        # Create ItemReadRelation object for indexing
        from app.support.item.schemas import ItemReadRelation
        
        item_read = ItemReadRelation(
            id=item.id,
            drink=item.drink,
            vol=item.vol,
            price=item.price,
            count=item.count,
            image_path=item.image_path,
            image_id=item.image_id
        )
        
        # Convert to dict for indexing
        doc_dict = item_read.model_dump(mode='python')
        
        # Update in Meilisearch
        await item_search_service.update_document(item_search_service.index_name, doc_dict)
        
        logger.info(f"Item {item.id} updated in index successfully after update")
    except Exception as e:
        logger.error(f"Error updating item {item.id} in index after update: {e}")


async def remove_item_from_index_after_deletion(item_id: int):
    """
    Hook to remove item from index after deletion
    """
    try:
        # Remove from Meilisearch
        await item_search_service.delete_item_from_search(item_id)
        
        logger.info(f"Item {item_id} removed from index successfully after deletion")
    except Exception as e:
        logger.error(f"Error removing item {item_id} from index after deletion: {e}")


async def trigger_incremental_sync(db: AsyncSession, since_datetime: Optional[datetime] = None):
    """
    Trigger incremental sync for items
    """
    try:
        await item_search_service.incremental_sync(db, since_datetime)
    except Exception as e:
        logger.error(f"Error during incremental sync: {e}")
        raise