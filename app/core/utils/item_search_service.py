"""
Item-specific search service with Meilisearch and Redis integration
"""
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, desc, or_
from sqlalchemy.future import select
from app.core.utils.meilisearch_service import meilisearch_service
from app.support.item.model import Item
from app.support.item.schemas import ItemReadRelation
from app.support.drink.model import Drink
from app.support.subcategory.model import Subcategory
from app.support.category.model import Category
from app.support.subregion.model import Subregion
from app.support.region.model import Region
from app.support.country.model import Country
from app.support.sweetness.model import Sweetness
from app.support.varietal.model import Varietal
from app.support.food.model import Food
from app.support.drink.model import DrinkFood, DrinkVarietal


class ItemSearchService:
    def __init__(self):
        self.index_name = "items"
        self.schema = ItemReadRelation

    async def initialize_index(self):
        """
        Initialize the items search index
        """
        await meilisearch_service.initialize_index(self.index_name, self.schema)

    async def sync_items_to_meilisearch(self, db: AsyncSession, batch_size: int = 100):
        """
        Sync all items to Meilisearch with relationships
        """
        try:
            # Get all item IDs first
            stmt = select(Item.id).order_by(Item.id)
            result = await db.execute(stmt)
            item_ids = [row.id for row in result.fetchall()]
            
            # Process in batches
            for i in range(0, len(item_ids), batch_size):
                batch_ids = item_ids[i:i + batch_size]
                
                # Load items with all relationships using selectinload
                items_stmt = (
                    select(Item)
                    .options(
                        selectinload(Item.drink)
                        .selectinload(Drink.subcategory)
                        .selectinload(Subcategory.category),
                        selectinload(Item.drink)
                        .selectinload(Drink.subregion)
                        .selectinload(Subregion.region)
                        .selectinload(Region.country),
                        selectinload(Item.drink)
                        .selectinload(Drink.sweetness),
                        selectinload(Item.drink)
                        .selectinload(Drink.food_associations)
                        .selectinload(DrinkFood.food),
                        selectinload(Item.drink)
                        .selectinload(Drink.varietal_associations)
                        .selectinload(DrinkVarietal.varietal),
                    )
                    .where(Item.id.in_(batch_ids))
                    .order_by(Item.id)
                )
                
                items_result = await db.execute(items_stmt)
                items = items_result.scalars().all()
                
                # Convert to pydantic models and serialize
                documents = []
                for item in items:
                    try:
                        # Create ItemReadRelation object
                        item_read = ItemReadRelation(
                            id=item.id,
                            drink=item.drink,
                            vol=item.vol,
                            price=item.price,
                            count=item.count,
                            image_path=item.image_path,
                            image_id=item.image_id
                        )
                        
                        # Serialize to dict
                        doc_dict = item_read.model_dump(mode='python')
                        documents.append(doc_dict)
                    except Exception as e:
                        logger.error(f"Error serializing item {item.id}: {e}")
                        continue
                
                # Index the batch
                if documents:
                    await meilisearch_service.index_documents_batch(self.index_name, documents)
                    
            logger.info(f"Successfully synced {len(item_ids)} items to Meilisearch")
        except Exception as e:
            logger.error(f"Error syncing items to Meilisearch: {e}")
            raise

    async def incremental_sync(self, db: AsyncSession, since_datetime: Optional[datetime] = None):
        """
        Incrementally sync only changed/added items since the last sync
        """
        try:
            if since_datetime is None:
                # Use a recent timestamp if none provided
                since_datetime = datetime.utcnow() - timedelta(hours=1)
            
            # Find items that were created or updated since the last sync
            stmt = (
                select(Item)
                .options(
                    selectinload(Item.drink)
                    .selectinload(Drink.subcategory)
                    .selectinload(Subcategory.category),
                    selectinload(Item.drink)
                    .selectinload(Drink.subregion)
                    .selectinload(Subregion.region)
                    .selectinload(Region.country),
                    selectinload(Item.drink)
                    .selectinload(Drink.sweetness),
                    selectinload(Item.drink)
                    .selectinload(Drink.food_associations)
                    .selectinload(DrinkFood.food),
                    selectinload(Item.drink)
                    .selectinload(Drink.varietal_associations)
                    .selectinload(DrinkVarietal.varietal),
                )
                .where(
                    or_(
                        Item.created_at >= since_datetime,
                        Item.updated_at >= since_datetime
                    )
                )
                .order_by(Item.updated_at)
            )
            
            result = await db.execute(stmt)
            changed_items = result.scalars().all()
            
            # Process changed items
            documents = []
            for item in changed_items:
                try:
                    # Create ItemReadRelation object
                    item_read = ItemReadRelation(
                        id=item.id,
                        drink=item.drink,
                        vol=item.vol,
                        price=item.price,
                        count=item.count,
                        image_path=item.image_path,
                        image_id=item.image_id
                    )
                    
                    # Serialize to dict
                    doc_dict = item_read.model_dump(mode='python')
                    documents.append(doc_dict)
                except Exception as e:
                    logger.error(f"Error serializing changed item {item.id}: {e}")
                    continue
            
            # Index the changed documents
            if documents:
                await meilisearch_service.index_documents_batch(self.index_name, documents)
                
            logger.info(f"Incrementally synced {len(changed_items)} items to Meilisearch")
        except Exception as e:
            logger.error(f"Error in incremental sync: {e}")
            raise

    async def search_items(self, query: str, limit: int = 20, offset: int = 0, filters: Optional[Dict] = None):
        """
        Search items in Meilisearch
        """
        filter_str = None
        if filters:
            # Build Meilisearch filter string from filters dict
            filter_parts = []
            for key, value in filters.items():
                if isinstance(value, (str, int, float)):
                    filter_parts.append(f"{key} = '{value}'" if isinstance(value, str) else f"{key} = {value}")
                elif isinstance(value, list):
                    if value:  # Only add filter if list is not empty
                        list_values = [f"'{v}'" if isinstance(v, str) else str(v) for v in value]
                        filter_parts.append(f"{key} IN [{', '.join(list_values)}]")
            if filter_parts:
                filter_str = " AND ".join(filter_parts)
        
        return await meilisearch_service.search(
            self.index_name, 
            query, 
            limit=limit, 
            offset=offset, 
            filter=filter_str
        )

    async def delete_item_from_search(self, item_id: int):
        """
        Delete item from search index when deleted from database
        """
        await meilisearch_service.delete_document(self.index_name, item_id)

    async def get_item_from_search(self, item_id: int) -> Optional[Dict[str, Any]]:
        """
        Get item from search index
        """
        return await meilisearch_service.get_document(self.index_name, item_id)


# Global instance
item_search_service = ItemSearchService()