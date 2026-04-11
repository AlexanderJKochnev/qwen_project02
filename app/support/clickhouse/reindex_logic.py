# app.support.clickhouse.reindex_logic.py
import json
from loguru import logger
from app.support.clickhouse.service import embedding_service


async def reindex_data(ch_client):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    
    def create_rag_string(row):
        # Принудительно к строке для безопасности
        name = str(row.get('name', ''))
        category = str(row.get('category', ''))
        
        header = f"Product: {name}. Category: {category}."
        if row.get('brand'): header += f" Brand: {row['brand']}."
        
        specs = ""
        if row.get('country'): specs += f" Country: {row['country']}."
        if row.get('abv'): specs += f" ABV: {row['abv']}%."
        
        desc = f" | Description: {row.get('description', '')}"
        
        attr_str = ""
        if row.get('attributes'):
            try:
                attrs = row['attributes']
                if isinstance(attrs, str): attrs = json.loads(attrs)
                if attrs and isinstance(attrs, dict):
                    attr_str = " | Attributes: " + ", ".join([f"{k}: {v}" for k, v in attrs.items()])
            except Exception:
                logger.warning("Failed to parse attributes in create_rag_string")
        
        return (header + specs + desc + attr_str)[:1000].strip()
    
    logger.info(f"Starting reindexing from {source_table} to {target_table}")
    
    try:
        # Для теста оставляем LIMIT 100. Для боя — убираем.
        query = f"SELECT * EXCEPT(embedding) FROM {source_table} LIMIT 100"
        settings = {'max_block_size': 10000}
        
        # Получаем контекст стрима
        stream_context = await ch_client.query_column_block_stream(query, settings = settings)
        
        async with stream_context as stream:
            # Названия колонок из источника
            column_names = list(stream.source.column_names)
            full_columns = column_names + ['embedding']
            total_count = 0
            
            async for block_rows in stream:
                # Превращаем кортежи из CH в словари для удобства обработки
                rows = [dict(zip(column_names, row)) for row in block_rows]
                
                # 1. Готовим тексты
                texts_to_embed = [create_rag_string(r) for r in rows]
                
                # 2. Генерируем эмбеддинги (batch_size для Xeon)
                embeddings_iter = embedding_service.model.embed(texts_to_embed, batch_size = 128)
                embeddings_list = [e.tolist() for e in embeddings_iter]
                
                # 3. Формируем финальный список кортежей для вставки
                final_data_to_insert = []
                for i, row in enumerate(rows):
                    # Добавляем вектор в словарь
                    row['embedding'] = embeddings_list[i]
                    
                    # Чистим JSON: ClickHouse-connect ожидает dict для типа JSON
                    attrs = row.get('attributes')
                    if isinstance(attrs, str):
                        try:
                            row['attributes'] = json.loads(attrs)
                        except Exception:
                            row['attributes'] = {}
                    elif attrs is None or not isinstance(attrs, dict):
                        row['attributes'] = {}
                    
                    # Превращаем в кортеж строго по списку колонок
                    final_data_to_insert.append(tuple(row[col] for col in full_columns))
                
                # 4. Асинхронная вставка списка кортежей
                await ch_client.insert(
                        target_table, final_data_to_insert, column_names = full_columns
                        )
                
                total_count += len(rows)
                logger.info(f"Successfully indexed {total_count} rows...")
        
        logger.success(f"Finish! Total {total_count} rows moved to {target_table}")
    
    except Exception as e:
        logger.exception(f"Reindexing failed: {e}")
        raise e
