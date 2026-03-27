import os
from asynch import connect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Item  # Импортируйте вашу модель SQLAlchemy


class SearchService:
    def __init__(self):
        self.ch_host = os.getenv("CH_HOST", "clickhouse")
        self.ch_user = os.getenv("CH_USER", "default")
        self.ch_pass = os.getenv("CH_PASSWORD", "password")
    
    async def get_ch_connection(self):
        return await connect(
                host = self.ch_host, port = 9000, user = self.ch_user, password = self.ch_pass, database = "default"
                )
    
    async def global_search(self, query: str, pg_db: AsyncSession, limit: int = 20):
        # 1. Поиск ID в ClickHouse
        # Разбиваем запрос на слова для multiSearchAny или ILIKE
        words = query.lower().split()
        if not words:
            return []
        
        # Формируем условия для каждого слова (чтобы работало AND)
        conditions = " AND ".join([f"search_content ILIKE '%{word}%'" for word in words])
        
        ch_conn = await self.get_ch_connection()
        async with ch_conn.cursor() as cursor:
            # Ищем только ID, это максимально быстро
            sql = f"SELECT id FROM items_search WHERE {conditions} LIMIT {limit}"
            await cursor.execute(sql)
            ch_result = await cursor.fetchall()
        
        await ch_conn.close()
        
        ids = [row[0] for row in ch_result]
        if not ids:
            return []
        
        # 2. Получение полных данных из PostgreSQL
        # Используем оператор IN для массовой выборки по ID
        stmt = select(Item).where(Item.id.in_(ids))
        result = await pg_db.execute(stmt)
        
        # Важно: Сортируем результат Postgres в том же порядке, что пришли ID из CH
        items = result.scalars().all()
        items_dict = {item.id: item for item in items}
        return [items_dict[i] for i in ids if i in items_dict]


search_service = SearchService()
