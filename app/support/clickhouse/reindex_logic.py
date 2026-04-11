import json
import uuid
from loguru import logger
from app.support.clickhouse.service import embedding_service


async def reindex_data(ch_client):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"

    # Тот самый формат строки, который мы утвердили
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
                # ClickHouse может вернуть dict или строку JSON
                attrs = row['attributes']
                if isinstance(attrs, str):
                    attrs = json.loads(attrs)
                attr_str = " | Attributes: " + ", ".join([f"{k}: {v}" for k, v in attrs.items()])
            except Exception as e:
                logger.error(f'ClickHouse может вернуть dict или строку JSON {e}')

        desc = f" | Description: {row.get('description', '')}"
        # Лимит 1000 символов для e5-small
        return (header + specs + desc + attr_str)[:1000].strip()

    logger.info(f"Starting reindexing from {source_table} to {target_table}")

    try:
        # Читаем данные блоками (по 5000 строк оптимально для RAM)
        query = f"SELECT * EXCEPT(embedding) FROM {source_table} LIMIT 100"

        # Получаем стрим блоков
        stream = ch_client.query_column_block_stream(query)

        total_count = 0
        for block in stream:
            # Превращаем блок в список словарей для обработки
            column_names = block.column_names
            rows = [dict(zip(column_names, row)) for row in block.result_rows]

            # 1. Формируем тексты для нейронки
            texts_to_embed = [create_rag_string(r) for r in rows]

            # 2. Генерируем эмбеддинги ПАЧКОЙ (это даст x5 к скорости на CPU)
            # Мы используем напрямую внутреннюю модель fastembed
            embeddings_iter = embedding_service.model.embed(texts_to_embed, batch_size=64)
            embeddings_list = [e.tolist() for e in embeddings_iter]

            # 3. Привязываем векторы обратно к строкам
            for i, row in enumerate(rows):
                row['embedding'] = embeddings_list[i]

                # Маленький фикс: если UUID пришел строкой, оставляем,
                # если объектом — clickhouse-connect сам его поймет.
                # Но JSON поле должно быть именно словарем.
                if isinstance(row.get('attributes'), str):
                    try:
                        row['attributes'] = json.loads(row['attributes'])
                    except Exception as e:
                        logger.error(f'парсинг json. {e}')
                        row['attributes'] = {}

            # 4. Массовая вставка в новую таблицу
            ch_client.insert(target_table, rows, column_names=column_names + ['embedding'])

            total_count += len(rows)
            logger.info(f"Successfully indexed {total_count} rows...")

        logger.success(f"Finish! Total {total_count} rows moved to {target_table}")

    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        raise e
