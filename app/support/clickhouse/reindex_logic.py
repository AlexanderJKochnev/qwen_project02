# app.support.clickhouse.reindex_logic.py
import json
import uuid
from loguru import logger
from app.support.clickhouse.service import embedding_service


async def reindex_data(ch_client):
    source_table = "beverages_rag"
    target_table = "beverages_rag_v2"
    
    def create_rag_string(row):
        # Принудительно приводим к строке, чтобы избежать ошибок с UUID в полях
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
        query = f"SELECT * EXCEPT(embedding) FROM {source_table} LIMIT 100"
        settings = {'max_block_size': 10000}
        
        stream_context = await ch_client.query_column_block_stream(query, settings = settings)
        
        async with stream_context as stream:
            # Превращаем кортеж в список сразу, чтобы избежать TypeError при сложении
            column_names = list(stream.source.column_names)
            total_count = 0
            
            async for block_rows in stream:
                rows = [dict(zip(column_names, row)) for row in block_rows]
                
                # Генерация текстов
                texts_to_embed = [create_rag_string(r) for r in rows]
                
                # Генерация эмбеддингов
                embeddings_iter = embedding_service.model.embed(texts_to_embed, batch_size = 128)
                embeddings_list = [e.tolist() for e in embeddings_iter]
                
                for i, row in enumerate(rows):
                    row['embedding'] = embeddings_list[i]
                    
                    # Чистим JSON для вставки
                    attrs = row.get('attributes')
                    if isinstance(attrs, str):
                        try:
                            row['attributes'] = json.loads(attrs)
                        except Exception:
                            row['attributes'] = {}
                    elif attrs is None or not isinstance(attrs, dict):
                        row['attributes'] = {}
                
                # Исправлено: теперь оба операнда — списки
                await ch_client.insert(
                        target_table, rows, column_names = column_names + ['embedding']
                        )
                
                total_count += len(rows)
                logger.info(f"Successfully indexed {total_count} rows...")
        
        logger.success(f"Finish! Total {total_count} rows moved to {target_table}")
    
    except Exception as e:
        logger.exception(f"Reindexing failed: {e}")
        raise e
