# app.support.clickhouse.import_service.repositories.beverage_repository.py


class BeverageRepository:
    def __init__(self, client):
        self.client = client

    async def ensure_table(self):
        await self.client.query("""CREATE TABLE IF NOT EXISTS beverages_rag (...)""")

    async def create(self, beverage, file_hash, source_file, embedding):
        await self.client.insert(...)

    async def file_exists(self, file_hash: str) -> bool:
        res = await self.client.query("SELECT COUNT(*) FROM beverages_rag WHERE file_hash = %(hash)s", {'hash': file_hash})
        return res.result_rows[0][0] > 0
