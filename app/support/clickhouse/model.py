# app.support.clickhouse.model.py
from loguru import logger
from app.core.config.database.click_async import get_ch_client


async def ensure_table_exists():
    """Создание таблицы в ClickHouse"""
    client = await get_ch_client(None)

    query = """
    DROP TABLE IF EXISTS beverages_rag_v2;
    CREATE TABLE beverages_rag_v2 (
        id UUID DEFAULT generateUUIDv4(),
        name String,
        description String,
        category LowCardinality(String),
        country Nullable(String),
        brand Nullable(String),
        abv Nullable(Float32),
        price Nullable(Decimal(10,2)),
        rating Nullable(Float32),
        attributes JSON,
        embedding Array(Float32),
        file_hash String,
        source_file String,
        created_at DateTime DEFAULT now(),
        -- Индекс для быстрого поиска по подстрокам и опечаткам (Вариант 1)
        INDEX idx_name_ngram name TYPE ngrambf_v1(3, 512, 2, 0) GRANULARITY 1,
        -- Векторный индекс для смысла (Вариант 2)
        INDEX idx_embedding embedding TYPE vector_similarity('hnsw', 'cosineDistance', 384) GRANULARITY 100
    ) ENGINE = MergeTree
    ORDER BY (category, name, created_at);
    """

    await client.query(query)
    logger("✅ Table 'beverages_rag' ready")
