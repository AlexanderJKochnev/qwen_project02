# индексация новой таблицы rag
import asyncio
from app.core.config.database.click_async import ClickHouseManager
from app.support.clickhouse.reindex_logic import reindex_data # твой код выше

async def main():
    manager = ClickHouseManager()
    client = await manager.connect()
    try:
        await reindex_data(client)
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())