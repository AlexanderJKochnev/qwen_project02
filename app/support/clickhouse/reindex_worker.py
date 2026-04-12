# app/support/clickhouse/reindex_worker.py
import asyncio
import time
from loguru import logger
from app.support.clickhouse.service import embedding_service

CREATE_TABLE_V2_SQL = """
CREATE TABLE IF NOT EXISTS beverages_rag_v2 (
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
    embedding Array(Float32), -- ТЕПЕРЬ ТУТ БУДЕТ 256
    file_hash String,
    source_file String,
    created_at DateTime DEFAULT now(),
    INDEX idx_embedding embedding TYPE vector_similarity('hnsw', 'cosineDistance', 256) GRANULARITY 100
) ENGINE = MergeTree ORDER BY (category, name, created_at)
"""


async def run_reindexing(ch_manager):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    batch_size = 5000

    try:
        client = await ch_manager.connect()
        await client.command(f"DROP TABLE IF EXISTS {target_table}")
        await client.command(CREATE_TABLE_V2_SQL)
    except Exception as e:
        logger.error(f"Init failed: {e}")
        return

    columns = ['id', 'name', 'description', 'category', 'country', 'brand', 'abv', 'attributes']
    all_cols = ['id', 'name', 'description', 'category', 'country', 'brand', 'abv', 'price', 'rating', 'attributes',
                'file_hash', 'source_file', 'created_at']

    while True:
        try:
            query = f"SELECT * FROM {source_table} WHERE id NOT IN (SELECT id FROM {target_table}) LIMIT {batch_size}"
            result = await client.query(query)
            if not result.result_rows:
                break

            # Транспонируем (твоя рабочая схема)
            block_rows = list(zip(*result.result_rows))
            rows = [dict(zip(result.column_names, row)) for row in block_rows]

            # Формируем текст: ТУПО склеиваем всё в одну строку
            texts = [f"{r['name']} {r['brand']} {r['category']} {r['country']} {r['description']}" for r in rows]

            # Инференс StaticModel на CPU (это будет ОЧЕНЬ быстро)
            vectors = embedding_service.model.encode(texts)

            final_data = []
            for i, row in enumerate(rows):
                row['embedding'] = vectors[i].tolist()
                final_data.append(tuple(row[col] for col in (result.column_names + ['embedding'])))

            await client.insert(target_table, final_data, column_names=result.column_names + ['embedding'])
            logger.info(f"Indexed {len(rows)} rows via StaticModel 256d")

        except Exception as e:
            logger.error(f"Error: {e}")
            await asyncio.sleep(5)
