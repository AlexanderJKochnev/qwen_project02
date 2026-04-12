# app/support/clickhouse/reindex_worker.py
import json
import asyncio
from loguru import logger
from app.support.clickhouse.service import embedding_service

# SQL скрипт для создания таблицы (фиксируем структуру и индексы здесь)
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
    -- Индекс для опечаток и подстрок (Вариант 1)
    INDEX idx_name_ngram name TYPE ngrambf_v1(3, 512, 2, 0) GRANULARITY 1,
    -- Векторный индекс для семантики (Вариант 2)
    INDEX idx_embedding embedding TYPE vector_similarity('hnsw', 'cosineDistance', 384) GRANULARITY 100
) ENGINE = MergeTree
ORDER BY (category, name, created_at)
"""


def create_hybrid_string(row):
    """
    Формирует строку для FastEmbed.
    Приоритет: Факты (Name/Brand) -> Мета -> Описание.
    """
    facts = []
    if row.get('name'):
        facts.append(f"Name: {row['name']}")
    if row.get('brand'):
        facts.append(f"Brand: {row['brand']}")
    if row.get('category'):
        facts.append(f"Category: {row['category']}")
    if row.get('country'):
        facts.append(f"Origin: {row['country']}")
    if row.get('abv'):
        facts.append(f"Alcohol: {row['abv']}%")

    # Собираем факты через точку, отделяем описание пайпом
    facts_part = ". ".join(facts)
    desc_part = str(row.get('description', ''))

    return f"{facts_part} | {desc_part}"[:1000].strip()


async def run_reindexing(ch_manager):
    """
    Основной воркер переиндексации с защитой от обрывов.
    """
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    batch_size = 2000

    # 1. Инициализация таблицы
    try:
        client = await ch_manager.connect()
        await client.command(CREATE_TABLE_SQL)
        logger.success(f"✅ Table {target_table} is ready (Created or already exists)")
    except Exception as e:
        logger.error(f"❌ Failed to ensure table {target_table}: {e}")
        return

    logger.info("🚀 Starting Safe Hybrid Reindexing (FastEmbed CPU)...")

    # Жесткий список колонок для исключения ошибок транспонирования
    columns = ['id', 'name', 'description', 'category', 'country', 'brand', 'abv', 'price', 'rating', 'attributes',
               'file_hash', 'source_file', 'created_at']
    full_cols = columns + ['embedding']

    while True:
        try:
            # Проверяем соединение
            if not ch_manager.client:
                await ch_manager.connect()
            client = ch_manager.client

            # 2. Выбираем ID, которых нет в v2 (Докачка)
            # Используем LIMIT для контроля RAM на Xeon
            query = f"""
                SELECT {", ".join(columns)} FROM {source_table}
                WHERE id NOT IN (SELECT id FROM {target_table})
                LIMIT {batch_size}
            """

            # Настройки для стабильности
            settings = {'select_sequential_consistency': 1, 'max_execution_time': 0, 'max_block_size': batch_size}

            result = await client.query(query, settings=settings)

            # Если данных больше нет — выходим
            if not result.result_rows:
                logger.success("🏁 REINDEXING COMPLETE! Target table is up to date.")
                break

            # 3. Транспонируем поколоночный блок в строки (fix 'dict' issues)
            block_rows = list(zip(*result.result_rows))
            rows = [dict(zip(columns, r)) for r in block_rows]

            # 4. Генерация эмбеддингов
            texts = [create_hybrid_string(r) for r in rows]

            try:
                # Напрямую используем модель из сервиса
                embeddings_iter = embedding_service.model.embed(texts, batch_size=128)
                embeddings_list = [e.tolist() for e in embeddings_iter]
            except Exception as inf_e:
                logger.error(f"⚠️ Inference error on batch: {inf_e}")
                await asyncio.sleep(2)
                continue

            # 5. Подготовка пачки к вставке
            final_data = []
            for i, row in enumerate(rows):
                row['embedding'] = embeddings_list[i]

                # Чистим JSON атрибуты
                attrs = row.get('attributes')
                if isinstance(attrs, str):
                    try:
                        row['attributes'] = json.loads(attrs)
                    except Exception:
                        row['attributes'] = {}
                elif attrs is None or not isinstance(attrs, dict):
                    row['attributes'] = {}

                # Собираем кортеж строго по списку full_cols
                final_data.append(tuple(row[col] for col in full_cols))

            # 6. Асинхронная вставка
            await client.insert(target_table, final_data, column_names=full_cols)

            # Логируем текущий прогресс
            count_v2 = await client.command(f"SELECT count() FROM {target_table}")
            logger.info(f"📊 Progress: {count_v2} rows in v2 (+{len(rows)} in this batch)")

        except Exception as e:
            logger.error(f"🔌 Connection or Logic Error: {e}. Retrying in 10s...")
            await asyncio.sleep(10)
