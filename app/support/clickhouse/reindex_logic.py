# app.support.clickhouse.reindex_logic.py
import json
from loguru import logger
from app.support.clickhouse.service import embedding_service


async def reindex_data(ch_client):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    
    # 1. Явно определяем список всех колонок КРОМЕ embedding
    # Убедись, что этот список совпадает с твоим CREATE TABLE
    columns_to_read = ['id', 'name', 'description', 'category', 'country', 'brand', 'abv', 'price', 'rating',
            'attributes', 'file_hash', 'source_file', 'created_at']
    full_columns_to_write = columns_to_read + ['embedding']
    
    def create_rag_string(row):
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
            except Exception: pass
        return (header + specs + desc + attr_str)[:1000].strip()
    
    logger.info(f"Starting reindexing from {source_table} to {target_table}")
    
    try:
        # 2. Читаем строго определенные колонки
        cols_query = ", ".join(columns_to_read)
        query = f"SELECT {cols_query} FROM {source_table} LIMIT 100"
        settings = {'max_block_size': 10000}
        
        stream_context = await ch_client.query_column_block_stream(query, settings = settings)
        
        async with stream_context as stream:
            total_count = 0
            async for block_rows in stream:
                # 3. Сопоставляем данные строго по нашему списку columns_to_read
                rows = [dict(zip(columns_to_read, row)) for row in block_rows]
                
                texts_to_embed = [create_rag_string(r) for r in rows]
                embeddings_iter = embedding_service.model.embed(texts_to_embed, batch_size = 128)
                embeddings_list = [e.tolist() for e in embeddings_iter]
                
                final_data_to_insert = []
                for i, row in enumerate(rows):
                    row['embedding'] = embeddings_list[i]
                    
                    # Фикс JSON
                    attrs = row.get('attributes')
                    if isinstance(attrs, str):
                        try: row['attributes'] = json.loads(attrs)
                        except Exception: row['attributes'] = {}
                    elif not isinstance(attrs, dict):
                        row['attributes'] = {}
                    
                    # 4. Собираем кортеж строго по списку full_columns_to_write
                    final_data_to_insert.append(tuple(row[col] for col in full_columns_to_write))
                
                # 5. Вставка
                await ch_client.insert(
                        target_table, final_data_to_insert, column_names = full_columns_to_write
                        )
                
                total_count += len(rows)
                logger.info(f"Successfully indexed {total_count} rows...")
        
        logger.success(f"Finish! Total {total_count} rows moved to {target_table}")
    
    except Exception as e:
        logger.exception(f"Reindexing failed: {e}")
        raise e
