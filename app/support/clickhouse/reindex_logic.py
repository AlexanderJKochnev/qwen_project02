import json
from loguru import logger
from app.support.clickhouse.service import embedding_service


async def reindex_data(ch_client):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"

    def create_rag_string(row):
        # 1. Заголовок (Name, Category, Brand)
        header = f"Product: {row['name']}. Category: {row['category']}."
        if row.get('brand'):
            header += f" Brand: {row['brand']}."

        # 2. Технические данные (Country, ABV)
        specs = ""
        if row.get('country'):
            specs += f" Country: {row['country']}."
        if row.get('abv'):
            specs += f" ABV: {row['abv']}%."

        # 3. Атрибуты из JSON (Ставим ПЕРЕД описанием, чтобы не обрезались)
        attr_str = ""
        if row.get('attributes'):
            try:
                attrs = row['attributes']
                if isinstance(attrs, str):
                    attrs = json.loads(attrs)
                if attrs:
                    attr_str = " | Attributes: " + ", ".join([f"{k}: {v}" for k, v in attrs.items()])
            except Exception as e:
                logger.warning(f"Attributes parse error: {e}")

        # 4. Описание (В самый конец, оно может быть длинным)
        desc = f" | Description: {row.get('description', '')}"

        # Сборка с лимитом 1000 символов (актуально для e5-small)
        # Порядок: Header -> Specs -> Attributes -> Description
        return (header + specs + desc + attr_str)[:1000].strip()

    logger.info(f"Starting reindexing from {source_table} to {target_table}")

    try:
        # Для теста оставляем LIMIT 100. Для боя — убираем.
        # Настройка max_block_size = 10000 оптимальна для твоего Xeon и 64GB RAM
        query = f"SELECT * EXCEPT(embedding) FROM {source_table} LIMIT 100"
        settings = {'max_block_size': 10000}

        # Получаем стрим блоков данных
        stream = ch_client.query_column_block_stream(query, settings=settings)

        total_count = 0
        for block in stream:
            column_names = block.column_names
            # Превращаем блок в список словарей
            rows = [dict(zip(column_names, row)) for row in block.result_rows]

            # 1. Формируем тексты для нейронки
            texts_to_embed = [create_rag_string(r) for r in rows]

            # 2. Генерируем эмбеддинги ПАЧКОЙ по 128 (оптимально для AVX2)
            # Убедись, что в embedding_service.model threads=14
            embeddings_iter = embedding_service.model.embed(texts_to_embed, batch_size=128)
            embeddings_list = [e.tolist() for e in embeddings_iter]

            # 3. Обрабатываем данные перед вставкой
            for i, row in enumerate(rows):
                row['embedding'] = embeddings_list[i]

                # Корректируем формат JSON для ClickHouse
                if isinstance(row.get('attributes'), str):
                    try:
                        row['attributes'] = json.loads(row['attributes'])
                    except Exception as e:
                        logger.error(f'Корректируем формат JSON для ClickHouse {e}')
                        row['attributes'] = {}
                elif row.get('attributes') is None:
                    row['attributes'] = {}

            # 4. Массовая вставка пачки
            ch_client.insert(target_table, rows, column_names=column_names + ['embedding'])

            total_count += len(rows)
            logger.info(f"Successfully indexed {total_count} rows...")

        logger.success(f"Finish! Total {total_count} rows moved to {target_table}")

    except Exception as e:
        logger.error(f"Reindexing failed: {e}")
        raise e
