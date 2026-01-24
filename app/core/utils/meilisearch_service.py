"""
Meilisearch service with Redis caching for dual-write and incremental synchronization
"""
import asyncio
import json
from typing import List, Dict, Any, Optional, Type, Union
from datetime import datetime, timedelta
from loguru import logger
import meilisearch
import redis.asyncio as redis
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import and_, or_, func
from app.core.config.project_config import settings
from app.core.utils.pydantic_key_extractor import extract_keys_with_blacklist


class MeilisearchService:
    def __init__(self):
        self.client = meilisearch.AsyncClient(
            settings.MEILISEARCH_URL, 
            settings.MEILISEARCH_MASTER_KEY
        )
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            decode_responses=True
        )
        self.searchable_attributes_cache_key = "meilisearch:searchable_attrs"

    async def initialize_index(self, index_name: str, schema: Type[BaseModel]):
        """
        Initialize Meilisearch index with proper searchable attributes
        """
        try:
            # Create or get the index
            index = self.client.index(index_name)
            
            # Extract searchable attributes from schema
            searchable_attrs = extract_keys_with_blacklist(
                schema, 
                blacklist=['vol', 'alc', 'price', 'id', 'updated_at', 'created_at', 'count']
            )
            
            # Update settings to make these attributes searchable
            await index.update_searchable_attributes(searchable_attrs)
            
            # Store searchable attributes in Redis for reference
            await self.redis_client.setex(
                f"{self.searchable_attributes_cache_key}:{index_name}",
                86400,  # 24 hours
                json.dumps(searchable_attrs)
            )
            
            logger.info(f"Index {index_name} initialized with {len(searchable_attrs)} searchable attributes")
            return index
        except Exception as e:
            logger.error(f"Error initializing index {index_name}: {e}")
            raise

    async def index_document(self, index_name: str, document: Dict[str, Any]):
        """
        Index a single document with dual-write to Redis cache
        """
        try:
            index = self.client.index(index_name)
            
            # Add to Meilisearch
            task = await index.add_documents([document])
            await self.client.wait_for_task(task.task_uid, timeout_in_ms=60000)
            
            # Cache in Redis for faster access
            doc_id = document.get("id")
            if doc_id:
                await self.redis_client.hset(
                    f"meilisearch:index:{index_name}", 
                    str(doc_id), 
                    json.dumps(document)
                )
            
            logger.debug(f"Document {doc_id} indexed successfully in {index_name}")
        except Exception as e:
            logger.error(f"Error indexing document: {e}")
            raise

    async def index_documents_batch(self, index_name: str, documents: List[Dict[str, Any]], batch_size: int = 1000):
        """
        Index documents in batches with dual-write to Redis
        """
        try:
            index = self.client.index(index_name)
            
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                
                # Add to Meilisearch
                task = await index.add_documents(batch)
                await self.client.wait_for_task(task.task_uid, timeout_in_ms=60000)
                
                # Cache in Redis
                for doc in batch:
                    doc_id = doc.get("id")
                    if doc_id:
                        await self.redis_client.hset(
                            f"meilisearch:index:{index_name}", 
                            str(doc_id), 
                            json.dumps(doc)
                        )
                
                logger.debug(f"Indexed batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            logger.info(f"Successfully indexed {len(documents)} documents in {index_name}")
        except Exception as e:
            logger.error(f"Error indexing documents batch: {e}")
            raise

    async def search(self, index_name: str, query: str, limit: int = 20, offset: int = 0, filter: Optional[str] = None):
        """
        Search documents in Meilisearch with Redis fallback
        """
        try:
            index = self.client.index(index_name)
            
            search_params = {
                "limit": limit,
                "offset": offset,
                "show_matches_position": True,
            }
            
            if filter:
                search_params["filter"] = filter
            
            search_result = await index.search(query, search_params)
            
            # Optionally cache search results in Redis
            cache_key = f"meilisearch:search:{index_name}:{query}:{limit}:{offset}"
            if filter:
                cache_key += f":{filter}"
                
            await self.redis_client.setex(
                cache_key, 
                300,  # 5 minutes cache
                json.dumps(search_result)
            )
            
            return search_result
        except Exception as e:
            logger.error(f"Error searching in Meilisearch: {e}")
            # Try to get from Redis cache if search failed
            cache_key = f"meilisearch:search:{index_name}:{query}:{limit}:{offset}"
            if filter:
                cache_key += f":{filter}"
                
            cached_result = await self.redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            raise

    async def delete_document(self, index_name: str, doc_id: Union[str, int]):
        """
        Delete document from both Meilisearch and Redis
        """
        try:
            index = self.client.index(index_name)
            
            # Delete from Meilisearch
            task = await index.delete_document(str(doc_id))
            await self.client.wait_for_task(task.task_uid, timeout_in_ms=30000)
            
            # Delete from Redis cache
            await self.redis_client.hdel(f"meilisearch:index:{index_name}", str(doc_id))
            
            logger.debug(f"Document {doc_id} deleted from {index_name}")
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            raise

    async def delete_documents_batch(self, index_name: str, doc_ids: List[Union[str, int]]):
        """
        Delete multiple documents from both Meilisearch and Redis
        """
        try:
            index = self.client.index(index_name)
            
            # Delete from Meilisearch
            task = await index.delete_documents([str(doc_id) for doc_id in doc_ids])
            await self.client.wait_for_task(task.task_uid, timeout_in_ms=60000)
            
            # Delete from Redis cache
            if doc_ids:
                await self.redis_client.hdel(f"meilisearch:index:{index_name}", *[str(doc_id) for doc_id in doc_ids])
            
            logger.info(f"Deleted {len(doc_ids)} documents from {index_name}")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise

    async def get_document(self, index_name: str, doc_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Get document from Meilisearch or Redis cache
        """
        try:
            # First try Redis cache
            cached_doc = await self.redis_client.hget(f"meilisearch:index:{index_name}", str(doc_id))
            if cached_doc:
                return json.loads(cached_doc)
            
            # Then try Meilisearch
            index = self.client.index(index_name)
            doc = await index.get_document(str(doc_id))
            
            # Cache in Redis
            await self.redis_client.hset(
                f"meilisearch:index:{index_name}", 
                str(doc_id), 
                json.dumps(doc)
            )
            
            return doc
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None

    async def update_document(self, index_name: str, document: Dict[str, Any]):
        """
        Update document in Meilisearch and Redis
        """
        return await self.index_document(index_name, document)

    async def close(self):
        """Close connections"""
        await self.client.aclose()
        await self.redis_client.close()


# Global instance
meilisearch_service = MeilisearchService()