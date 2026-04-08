# app.support.clickhouse.model.py
from loguru import logger
from app.core.config.database.click_async import get_ch_client


async def ensure_table_exists():
    """Создание таблицы в ClickHouse"""
    client = await get_ch_client(None)

    query = """
    CREATE TABLE IF NOT EXISTS beverages_rag (
        id UUID DEFAULT generateUUIDv4(),
        name String,
        description String,
        category LowCardinality(String),
        country String,
        brand String,
        abv Nullable(Float32),
        price Nullable(Decimal(10,2)),
        volume_ml Nullable(UInt16),
        rating Nullable(Float32),
        rate_count Nullable(UInt32),
        attributes JSON,
        embedding Array(Float32),
        file_hash String,
        source_file String,
        created_at DateTime DEFAULT now(),
        INDEX idx_category (category) TYPE minmax GRANULARITY 1,
        INDEX idx_embedding embedding TYPE vector_similarity('hnsw', 'cosineDistance', 384) GRANULARITY 100
    ) ENGINE = MergeTree
    ORDER BY (category, name, created_at)
    """

    await client.query(query)
    logger("✅ Table 'beverages_rag' ready")
