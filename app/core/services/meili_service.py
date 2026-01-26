# app.core.services.meili_service.py
from fastapi import Depends
from typing import Type, TypeVar, List, Any, Generic
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from meilisearch_python_sdk import AsyncClient
from meilisearch_python_sdk.index import Index
from meilisearch_python_sdk.models.settings import MeilisearchSettings
from app.core.utils.pydantic_utils import get_pyschema, get_repo
from app.core.utils.pydantic_key_extractor import extract_keys_with_blacklist
from app.core.config.database.db_async import get_db
from app.support.item.service import ItemService
from app.support.item.schemas import ItemReadRelation

T = TypeVar("T", bound=BaseModel)


class BaseMeiliService(Generic[T]):
    def __init__(
            self, sqla_model: Any, pydantic_schema: Type[T]
    ):
        self.sqla_model = sqla_model
        self.index_name = sqla_model.__name__.lower()
        self.schema = get_pyschema(sqla_model, 'ReadRelation')
        self.repository = get_repo(sqla_model)

        self.searchable_attributes = extract_keys_with_blacklist(
            self.schema, blacklist=['vol', 'alc', 'price', 'id', 'updated_at', 'created_at', 'count']
        )
        self.after_date = (datetime.now(timezone.utc) - relativedelta(years=100)).isoformat()
        self._primary_key = "id"  # По умолчанию для Meilisearch

    async def get_index_instance(self, client: AsyncClient) -> Index:
        """Получает объект индекса без запроса к серверу."""
        return client.index(self.index_name)

    async def init_index(self, client: AsyncClient, db_session: AsyncSession):
        """
        Проверяет наличие индекса. Если его нет — создает и заполняет.
        Вызывается в lifespan или при первом обращении.
        """
        try:
            # Проверяем физическое наличие индекса на сервере
            await client.get_index(self.index_name)
        except Exception:
            # Если индекса нет (ошибка 404), создаем и выполняем Initial Load
            print(f"Index {self.index_name} not found. Starting initial load...")
            await self.rebuild_index(client, db_session)

    async def rebuild_index(self, client: AsyncClient, db_session: AsyncSession):
        """Полное пересоздание и заполнение индекса данными из БД."""
        # 1. Создаем индекс (или получаем существующий)
        index = await client.get_or_create_index(self.index_name, primary_key=self._primary_key)

        # 2. Очищаем старые данные
        await index.delete_all_documents()

        # 3. Настраиваем поиск
        await index.update_searchable_attributes(self.searchable_attributes)

        # 4. Выгружаем все данные из БД
        """  СЮДА ЗАГРУЖАЕМ ДАННЫЕ  """
        db_objs = await ItemService.get(self.after_date, self.repository, self.sqla_model, db_session)
        # result = await db_session.execute(select(self.sqla_model))
        # db_objs = result.scalars().all()

        if db_objs:
            # Валидируем через Pydantic для соблюдения структуры
            documents = [
                self.schema.model_validate(obj).model_dump(mode='json')
                for obj in db_objs
            ]
            # Массовая загрузка
            await index.add_documents(documents)

    async def search(self, client: AsyncClient, query: str, limit: int = 20):
        index = client.index(self.index_name)
        return await index.search(query, limit=limit)

    # --- Dual-Write методы (используются в репозитории) ---

    async def upsert_document(self, client: AsyncClient, db_obj: Any):
        """Добавление или обновление записи (синхронизация после коммита БД)"""
        index = client.index(self.index_name)
        document = self.schema.model_validate(db_obj).model_dump(mode='json')
        await index.add_documents([document])

    async def delete_document(self, client: AsyncClient, document_id: Any):
        """Удаление записи из индекса"""
        index = client.index(self.index_name)
        await index.delete_document(str(document_id))


class ItemMeiliService(BaseMeiliService[ItemReadRelation]):
    def __init__(self):
        from app.support.item.model import Item
        super().__init__(Item, ItemReadRelation)
        
    async def search(self, client: AsyncClient, query: str, page: int = 1, page_size: int = 20, lang: str = 'en'):
        """Поиск с пагинацией в Meilisearch"""
        index = client.index(self.index_name)
        offset = (page - 1) * page_size
        search_results = await index.search(
            query, 
            offset=offset, 
            limit=page_size,
            show_matches_position=True
        )
        
        total = search_results.estimated_total_hits or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1
        
        return {
            'results': search_results.hits,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }
    
    async def search_all(self, client: AsyncClient, query: str, lang: str = 'en'):
        """Поиск без пагинации в Meilisearch"""
        index = client.index(self.index_name)
        search_results = await index.search(
            query,
            limit=1000,  # Max reasonable limit for non-paginated results
            show_matches_position=True
        )
        
        return search_results.hits
    
    async def search_with_pagination(self, query: str, lang: str = 'en', page: int = 1, page_size: int = 20, session: AsyncSession = None):
        """Search method with pagination for the router"""
        from app.core.config.database.meili_async import get_meili_client
        async with get_meili_client() as client:
            result = await self.search(client, query, page, page_size, lang)
            
            # Convert results to PaginatedResponse format
            from app.core.schemas.base import PaginatedResponse
            paginated_result = PaginatedResponse(
                results=result['results'],
                total=result['total'],
                page=result['page'],
                page_size=result['page_size'],
                total_pages=result['total_pages']
            )
            return paginated_result
    
    async def search_without_pagination(self, query: str, lang: str = 'en', session: AsyncSession = None):
        """Search method without pagination for the router"""
        from app.core.config.database.meili_async import get_meili_client
        async with get_meili_client() as client:
            result = await self.search_all(client, query, lang)
            return result
