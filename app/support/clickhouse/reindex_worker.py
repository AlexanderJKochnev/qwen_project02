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

    # Явно задаем колонки, чтобы порядок в SELECT и словаре был идентичен
    columns = ['id', 'name', 'description', 'category', 'country', 'brand', 'abv', 'price', 'rating', 'attributes',
               'file_hash', 'source_file', 'created_at']
    full_columns = columns + ['embedding']

    try:
        client = await ch_manager.connect()
        await client.command(CREATE_TABLE_SQL)
        logger.success(f"✅ Table {target_table} ready")
    except Exception as e:
        logger.exception(f"❌ Failed to ensure table {target_table}: {e}")
        return

    logger.info("🚀 Starting 256d Reindexing (StaticModel)...")

    while True:
        try:
            if not ch_manager.client:
                await ch_manager.connect()
            client = ch_manager.client

            # 1. Читаем данные. NOT IN гарантирует, что мы не дублируем записи.
            query = f"SELECT {', '.join(columns)} FROM {source_table} WHERE id NOT IN (SELECT id FROM {target_table}) LIMIT {batch_size}"
            result = await client.query(query, settings={'select_sequential_consistency': 1})

            if not result.result_rows:
                logger.success("🏁 All records reindexed (256d)!")
                break

            # 2. Обработка колоночного вывода
            # col_data[0] - это все ID, col_data[1] - все Name и т.д.
            col_data = result.result_rows
            num_rows = len(col_data[0])

            rows = []
            for i in range(num_rows):
                row = {}
                for col_idx, col_name in enumerate(columns):
                    val = col_data[col_idx][i]
                    # Принудительно в строку для текстовых полей, чтобы не было TypeError в драйвере
                    if col_name in ['name', 'description', 'category', 'brand', 'country']:
                        row[col_name] = str(val) if val is not None else ""
                    else:
                        row[col_name] = val
                rows.append(row)

            # 3. Подготовка текстов для эмбеддингов
            texts = [f"{r['name']} {r['brand']} {r['category']} {r['description']}" for r in rows]

            # 4. Генерация векторов
            t_start = time.time()
            try:
                vectors = embedding_service.model.encode(texts)
            except Exception as e:
                logger.exception(f"Model encode failed: {e}")
                await asyncio.sleep(5)
                continue
            t_end = time.time()

            # 5. Сборка финального батча
            final_data = []
            for i, row in enumerate(rows):
                row['embedding'] = vectors[i].tolist()

                # Парсинг JSON поля attributes
                attrs = row.get('attributes')
                if isinstance(attrs, str):
                    try:
                        row['attributes'] = json.loads(attrs)
                    except Exception as e:
                        logger.error(f"JSON Parse error at row {row.get('id')}: {e}")
                        row['attributes'] = {}
                elif attrs is None or not isinstance(attrs, dict):
                    row['attributes'] = {}

                # Собираем кортеж СТРОГО в порядке full_columns
                final_data.append(tuple(row[col] for col in full_columns))

            # 6. Вставка в ClickHouse
            try:
                await client.insert(target_table, final_data, column_names=full_columns)
            except Exception as e:
                logger.exception(f"ClickHouse insert failed: {e}")
                await asyncio.sleep(10)
                continue

            logger.info(f"Indexed {len(rows)} rows. Neural speed: {len(rows) / (t_end - t_start):.1f} r/s")

        except Exception as e:
            logger.exception(f"🔌 Worker main loop error: {e}")
            await asyncio.sleep(10)
