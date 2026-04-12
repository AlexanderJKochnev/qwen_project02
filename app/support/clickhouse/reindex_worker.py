# app/support/clickhouse/reindex_worker.py
import json
import asyncio
import time
from loguru import logger
from app.support.clickhouse.service import embedding_service

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


async def run_reindexing(ch_manager):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    batch_size = 5000

    # 1. Подготовка таблицы
    try:
        client = await ch_manager.connect()
        await client.command(CREATE_TABLE_SQL)
        logger.success(f"✅ Table {target_table} ready (256d)")
    except Exception as e:
        logger.error(f"❌ Table init failed: {e}")
        return

    logger.info("🚀 Starting 256d Reindexing via StaticModel (Model2Vec)...")

    while True:
        try:
            if not ch_manager.client:
                await ch_manager.connect()
            client = ch_manager.client

            # 2. Выбираем ID, которых нет в v2
            query = f"SELECT * EXCEPT(embedding) FROM {source_table} WHERE id NOT IN (SELECT id FROM {target_table}) LIMIT {batch_size}"
            result = await client.query(query, settings={'select_sequential_consistency': 1})

            if not result.result_rows:
                logger.success("🏁 All records reindexed (256d)!")
                break

            # 3. Транспонируем колонки в строки
            # Исправлено: забираем названия колонок из результата
            column_names = list(result.column_names)
            block_rows = list(zip(*result.result_rows))
            rows = [dict(zip(column_names, row)) for row in block_rows]

            # 4. Формируем тексты (простая склейка без спец. префиксов)
            texts = [f"{r.get('name', '')} {r.get('brand', '')} {r.get('category', '')} {r.get('description', '')}" for
                     r in rows]

            # 5. Генерация векторов (StaticModel летает на CPU)
            t_start = time.time()
            vectors = embedding_service.model.encode(texts)
            t_end = time.time()

            # 6. Сборка кортежей для вставки
            final_batch = []
            full_columns = column_names + ['embedding']

            for i, row in enumerate(rows):
                row['embedding'] = vectors[i].tolist()

                # Фикс JSON
                attrs = row.get('attributes')
                if isinstance(attrs, str):
                    try:
                        row['attributes'] = json.loads(attrs)
                    except:
                        row['attributes'] = {}
                elif attrs is None:
                    row['attributes'] = {}

                # Собираем кортеж СТРОГО по списку имен
                final_batch.append(tuple(row[col] for col in full_columns))

            # 7. Вставка
            await client.insert(target_table, final_batch, column_names=full_columns)

            logger.info(f"Indexed {len(rows)} rows. Inference speed: {len(rows) / (t_end - t_start):.1f} r/s")

        except Exception as e:
            logger.error(f"🔌 Worker Error: {e}. Retrying in 10s...")
            await asyncio.sleep(10)
