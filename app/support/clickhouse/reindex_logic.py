import json
from loguru import logger
from app.support.clickhouse.service import embedding_service


async def reindex_data(ch_client):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"

    def create_rag_string(row):
        header = f"Product: {row['name']}. Category: {row['category']}."
        if row.get('brand'):
            header += f" Brand: {row['brand']}."

        specs = ""
        if row.get('country'):
            specs += f" Country: {row['country']}."
        if row.get('abv'):
            specs += f" ABV: {row['abv']}%."

        attr_str = ""
        if row.get('attributes'):
            try:
                attrs = row['attributes']
                if isinstance(attrs, str):
                    attrs = json.loads(attrs)
                if attrs:
                    attr_str = " | Attributes: " + ", ".join([f"{k}: {v}" for k, v in attrs.items()])
            except Exception as e:
                logger.error(f'row attributes {e}')
                pass

        desc = f" | Description: {row.get('description', '')}"
        return (header + specs + desc + attr_str)[:1000].strip()

    logger.info(f"Starting reindexing from {source_table} to {target_table}")

    try:
        query = f"SELECT * EXCEPT(embedding) FROM {source_table} LIMIT 100"
        settings = {'max_block_size': 10000}

        # В асинхронном клиенте вызываем await на сам стрим
        async with await ch_client.query_column_block_stream(query, settings=settings) as stream:
            # Названия колонок забираем у самого объекта стрима
            column_names = stream.column_names
            total_count = 0

            # Асинхронно итерируемся по блокам данных (спискам строк)
            async for block_rows in stream:
                # block_rows — это список кортежей (данные)
                rows = [dict(zip(column_names, row)) for row in block_rows]

                # 1. Тексты для эмбеддингов
                texts_to_embed = [create_rag_string(r) for r in rows]

                # 2. Генерация векторов (синхронная операция, batch_size для Xeon)
                embeddings_iter = embedding_service.model.embed(texts_to_embed, batch_size=128)
                embeddings_list = [e.tolist() for e in embeddings_iter]

                # 3. Подготовка к вставке
                for i, row in enumerate(rows):
                    row['embedding'] = embeddings_list[i]
                    # ClickHouse JSON поле должно быть dict
                    if isinstance(row.get('attributes'), str):
                        try:
                            row['attributes'] = json.loads(row['attributes'])
                        except Exception as e:
                            logger.error(f'row attributes2 {e}')
                            row['attributes'] = {}
                    elif row.get('attributes') is None:
                        row['attributes'] = {}

                # 4. Асинхронная вставка
                await ch_client.insert(target_table, rows, column_names=column_names + ['embedding'])

                total_count += len(rows)
                logger.info(f"Successfully indexed {total_count} rows...")

        logger.success(f"Finish! Total {total_count} rows moved to {target_table}")

    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        raise e
