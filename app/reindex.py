# reindex.py
# запуск docker compose exec -it app python -m app.reindex
import asyncio
from app.core.config.database.click_async import ClickHouseManager
from app.support.clickhouse.reindex_logic import reindex_data
from app.support.clickhouse.reindex_worker import run_reindexing


async def main():
    manager = ClickHouseManager()
    # client = await manager.connect()
    try:
        await run_reindexing(manager)
        # await reindex_data(client)
    finally:
        await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
