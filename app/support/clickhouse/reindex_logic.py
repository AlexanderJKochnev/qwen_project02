# app.support.clickhouse.reindex_logic.py
import json
from loguru import logger
from app.support.clickhouse.service import embedding_service


async def reindex_data(ch_client):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    
    # Порядок важен
    columns = ['id', 'name', 'description', 'category', 'country', 'brand', 'abv', 'price', 'rating', 'attributes',
            'file_hash', 'source_file', 'created_at']
    
    def create_rag_string(row):
        name = str(row.get('name', ''))
        cat = str(row.get('category', ''))
        header = f"Product: {name}. Category: {cat}."
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
                if isinstance(attrs, dict):
                    attr_str = " | Attributes: " + ", ".join([f"{k}: {v}" for k, v in attrs.items()])
            except Exception: pass
        
        return (header + specs + desc + attr_str)[:1000].strip()
    
    logger.info("Starting reindexing (Column-to-Row conversion)...")
    
    try:
        col_names_str = ", ".join(columns)
        query = f"SELECT {col_names_str} FROM {source_table} LIMIT 100"
        
        async with await ch_client.query_column_block_stream(query) as stream:
            total_count = 0
            async for block_columns in stream:
                # ВАЖНО: block_columns — это список СТОЛБЦОВ.
                # Транспонируем их в СТРОКИ:
                block_rows = list(zip(*block_columns))
                
                # Теперь block_rows — это список кортежей-строк, и zip с именами сработает:
                rows = [dict(zip(columns, row)) for row in block_rows]
                
                # 1. Тексты для эмбеддингов
                texts = [create_rag_string(r) for r in rows]
                
                # 2. Генерация векторов
                emb_gen = embedding_service.model.embed(texts, batch_size = 128)
                embeddings = [e.tolist() for e in emb_gen]
                
                # 3. Сборка финальных кортежей для вставки
                final_batch = []
                full_cols = columns + ['embedding']
                
                for i, row in enumerate(rows):
                    row['embedding'] = embeddings[i]
                    
                    # Фикс JSON для ClickHouse
                    if isinstance(row.get('attributes'), str):
                        try: row['attributes'] = json.loads(row['attributes'])
                        except Exception: row['attributes'] = {}
                    elif row.get('attributes') is None:
                        row['attributes'] = {}
                    
                    # Собираем кортеж в правильном порядке
                    final_batch.append(tuple(row[col] for col in full_cols))
                
                # 4. Вставка
                await ch_client.insert(target_table, final_batch, column_names = full_cols)
                
                total_count += len(rows)
                logger.info(f"Successfully indexed {total_count} rows...")
        
        logger.success("Reindexing finished!")
    
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        raise e
