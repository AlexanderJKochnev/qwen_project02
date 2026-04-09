#!/usr/bin/env python3
import asyncio
# from loguru import logger
from pathlib import Path
from .click_async import ClickHouseManager
from .parsers import PARSERS
from .import_service import ImportService
from .beverage_repository import BeverageRepository


async def main():
    ch = ClickHouseManager()  # host="clickhouse", port=8123, user="default", password="")
    await ch.connect()
    repo = BeverageRepository(ch.client)
    await repo.ensure_table()
    importer = ImportService(repo, data_dir=Path("/app/data"), cache_dir=Path("/app/cache"))
    for name, parser in [('beer_data.csv', PARSERS['beer_data.csv']), ...]:  # все 7 файлов
        if (Path("/app/data") / name).exists():
            await importer.import_file(name, parser)
    await ch.close()

if __name__ == "__main__":
    asyncio.run(main())
