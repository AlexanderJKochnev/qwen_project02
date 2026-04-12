# app/support/clickhouse/reindex_worker.py
# app/support/clickhouse/reindex_worker.py
import json
import asyncio
import time
from loguru import logger
from app.support.clickhouse.service import embedding_service

# Фиксируем структуру таблицы под 256 измерений
CREATE_TABLE_SQL = """
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
    embedding Array(Float32),
    file_hash String,
    source_file String,
    created_at DateTime DEFAULT now(),
    INDEX idx_embedding embedding TYPE vector_similarity('hnsw', 'cosineDistance', 256) GRANULARITY 100
) ENGINE = MergeTree
ORDER BY (category, name, created_at)
"""


def create_simple_string(row):
    """Тупая склейка для StaticModel (Model2Vec)"""
    name = str(row.get('name', ''))
    brand = str(row.get('brand', ''))
    cat = str(row.get('category', ''))
    desc = str(row.get('description', ''))
    # Просто слова через пробел — для статической модели этого достаточно
    return f"{name} {brand} {cat} {desc}"[:1000].strip()


async def run_reindexing(ch_manager):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    batch_size = 5000

    try:
        client = await ch_manager.connect()
        await client.command(CREATE_TABLE_SQL)
        logger.success(f"✅ Table {target_table} ready (256d)")
    except Exception:
        logger.exception("❌ Table init failed")
        return

    # Жесткий список колонок для синхронизации zip
    columns = ['id', 'name', 'description', 'category', 'country', 'brand', 'abv', 'price', 'rating', 'attributes',
               'file_hash', 'source_file', 'created_at']
    full_columns = columns + ['embedding']

    logger.info("🚀 Starting 256d Reindexing via StaticModel (Proven Logic)...")

    while True:
        try:
            if not ch_manager.client:
                await ch_manager.connect()
            client = ch_manager.client

            # Читаем строго заданные колонки
            query = f"SELECT {', '.join(columns)} FROM {source_table} WHERE id NOT IN (SELECT id FROM {target_table}) LIMIT {batch_size}"
            result = await client.query(query, settings={'select_sequential_consistency': 1, 'max_execution_time': 0})

            if not result.result_rows:
                logger.success("🏁 All records reindexed!")
                break

            # --- ТА САМАЯ РАБОЧАЯ МЕХАНИКА ---
            block_rows = list(zip(*result.result_rows))
            rows = [dict(zip(columns, row)) for row in block_rows]
            # ---------------------------------

            # Генерация векторов (Model2Vec на CPU)
            texts = [create_simple_string(r) for r in rows]
            t_start = time.time()
            try:
                # Векторизация 256d
                vectors = embedding_service.model.encode(texts)
            except Exception:
                logger.exception("Inference error")
                continue
            t_end = time.time()

            # Сборка финальных кортежей
            final_batch = []
            for i, row in enumerate(rows):
                row['embedding'] = vectors[i].tolist()

                # Чистим JSON
                attrs = row.get('attributes')
                if isinstance(attrs, str):
                    try:
                        row['attributes'] = json.loads(attrs)
                    except:
                        row['attributes'] = {}
                elif attrs is None or not isinstance(attrs, dict):
                    row['attributes'] = {}

                final_batch.append(tuple(row[col] for col in full_columns))

            # Вставка
            await client.insert(target_table, final_batch, column_names=full_columns)

            logger.info(f"Indexed {len(rows)} rows. Neural speed: {len(rows) / (t_end - t_start):.1f} r/s")

        except Exception:
            logger.exception("🔌 Worker Loop Error")
            await asyncio.sleep(10)
