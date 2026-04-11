# app.support.clickhouse.reindex_logic.py
import json
from loguru import logger
from app.support.clickhouse.service import embedding_service


async def reindex_data(ch_client):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    
    def create_rag_string(row):
        header = f"Product: {row['name']}. Category: {row['category']}."
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
                if attrs:
                    attr_str = " | Attributes: " + ", ".join([f"{k}: {v}" for k, v in attrs.items()])
            except Exception:
                logger.warning("Failed to parse attributes in create_rag_string")
        
        return (header + specs + desc + attr_str)[:1000].strip()
    
    logger.info(f"Starting reindexing from {source_table} to {target_table}")
    
    try:
        query = f"SELECT * EXCEPT(embedding) FROM {source_table} LIMIT 100"
        settings = {'max_block_size': 10000}
        
        # 1. Сначала дожидаемся создания контекстного менеджера
        stream_context = await ch_client.query_column_block_stream(query, settings = settings)
        
        # 2. Входим в контекст через async with
        async with stream_context as stream:
            # Названия колонок у асинхронного стрима лежат в stream.source.column_names
            column_names = stream.source.column_names
            total_count = 0
            
            async for block_rows in stream:
                rows = [dict(zip(column_names, row)) for row in block_rows]
                texts_to_embed = [create_rag_string(r) for r in rows]
                
                # Генерация эмбеддингов
                embeddings_iter = embedding_service.model.embed(texts_to_embed, batch_size = 128)
                embeddings_list = [e.tolist() for e in embeddings_iter]
                
                for i, row in enumerate(rows):
                    row['embedding'] = embeddings_list[i]
                    if isinstance(row.get('attributes'), str):
                        try:
                            row['attributes'] = json.loads(row['attributes'])
                        except Exception as e:
                            logger.error(f"JSON parse error: {e}")
                            row['attributes'] = {}
                    elif row.get('attributes') is None:
                        row['attributes'] = {}
                
                # Асинхронная вставка
                await ch_client.insert(target_table, rows, column_names = column_names + ['embedding'])
                
                total_count += len(rows)
                logger.info(f"Successfully indexed {total_count} rows...")
        
        logger.success(f"Finish! Total {total_count} rows moved to {target_table}")
    
    except Exception as e:
        logger.exception(f"Reindexing failed with error: {e}")
        raise e
