# app/support/clickhouse/reindex_worker.py
import json
import asyncio
import time
from loguru import logger
from app.support.clickhouse.service import embedding_service

# SQL скрипт для создания таблицы (фиксируем здесь для анналов)
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
    INDEX idx_name_ngram name TYPE ngrambf_v1(3, 512, 2, 0) GRANULARITY 1,
    INDEX idx_embedding embedding TYPE vector_similarity('hnsw', 'cosineDistance', 384) GRANULARITY 100
) ENGINE = MergeTree
ORDER BY (category, name, created_at)
"""


def create_hybrid_string(row):
    """Формирует строку для FastEmbed (Header -> Specs -> Description -> Attributes)"""
    name = str(row.get('name', ''))
    cat = str(row.get('category', ''))

    header = f"Product: {name}. Category: {cat}."
    if row.get('brand'):
        header += f" Brand: {row['brand']}."

    specs = ""
    if row.get('country'):
        specs += f" Country: {row['country']}."
    if row.get('abv'):
        specs += f" ABV: {row['abv']}%."

    desc = f" | Description: {row.get('description', '')}"

    attr_str = ""
    if row.get('attributes'):
        try:
            attrs = row['attributes']
            if isinstance(attrs, str):
                attrs = json.loads(attrs)
            if isinstance(attrs, dict):
                attr_str = " | Attributes: " + ", ".join([f"{k}: {v}" for k, v in attrs.items()])
        except Exception as e:
            logger.error(f"Attr parse error: {e}")

    return (header + specs + desc + attr_str)[:1000].strip()


async def run_reindexing(ch_manager):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    batch_size = 2000

    # 1. Подготовка таблицы
    try:
        client = await ch_manager.connect()
        await client.command(CREATE_TABLE_SQL)
        logger.success(f"✅ Table {target_table} ready")
    except Exception as e:
        logger.error(f"❌ Table creation failed: {e}")
        return

    columns = ['id', 'name', 'description', 'category', 'country', 'brand', 'abv', 'price', 'rating', 'attributes',
               'file_hash', 'source_file', 'created_at']
    full_columns = columns + ['embedding']

    logger.info("🚀 Starting Safe Hybrid Reindexing (FastEmbed CPU)...")

    while True:
        try:
            # Проверка/Восстановление соединения
            if not ch_manager.client:
                await ch_manager.connect()
            client = ch_manager.client

            # 2. Докачка: выбираем только отсутствующие ID
            query = f"""
                SELECT {', '.join(columns)} FROM {source_table}
                WHERE id NOT IN (SELECT id FROM {target_table})
                LIMIT {batch_size}
            """
            settings = {'max_block_size': batch_size, 'max_execution_time': 0}

            # Используем проверенный вчера асинхронный стрим
            async with await client.query_column_block_stream(query, settings=settings) as stream:
                total_in_batch = 0

                async for block_columns in stream:
                    t_start = time.time()

                    # --- РАБОЧАЯ МЕХАНИКА ВЧЕРАШНЕГО ДНЯ ---
                    # 1. Транспонируем колонки в строки
                    block_rows = list(zip(*block_columns))
                    rows = [dict(zip(columns, row)) for row in block_rows]
                    # ---------------------------------------

                    if not rows:
                        continue

                    # 3. Эмбеддинги (FastEmbed CPU)
                    texts = [create_hybrid_string(r) for r in rows]
                    try:
                        embeddings_iter = embedding_service.model.embed(texts, batch_size=256)
                        embeddings = [e.tolist() for e in embeddings_iter]
                    except Exception as e:
                        logger.error(f"Inference error: {e}")
                        continue

                    # 4. Сборка для вставки
                    final_batch = []
                    for i, row in enumerate(rows):
                        row['embedding'] = embeddings[i]

                        # Фикс JSON
                        attrs = row.get('attributes')
                        if isinstance(attrs, str):
                            try:
                                row['attributes'] = json.loads(attrs)
                            except Exception as e:
                                logger.error(f'ERROR1 {e}')
                                row['attributes'] = {}
                        elif attrs is None:
                            row['attributes'] = {}

                        final_batch.append(tuple(row[col] for col in full_columns))

                    # 5. Вставка
                    await client.insert(target_table, final_batch, column_names=full_columns)

                    total_in_batch += len(rows)
                    t_end = time.time()
                    logger.info(f"Indexed {len(rows)} rows. Speed: {len(rows) / (t_end - t_start):.1f} r/s")

                # Если после прохода стрима в этом цикле ничего не пришло — значит всё
                if total_in_batch == 0:
                    logger.success("🏁 ALL DONE. No more records to reindex.")
                    return

        except Exception as e:
            logger.error(f"🔌 Worker Error: {e}. Retrying in 10s...")
            await asyncio.sleep(10)
