# DOCS/trigram_index.md
1. trigram index (применяется в Item)
   1. Как проверить подкючение trigram 
       SELECT *
       FROM pg_extension;
   2. Как проверить наличие индекса:
       SELECT tablename, indexname, indexdef
       FROM pg_indexes
       WHERE tablename = 'items' AND indexname = 'idx_items_search_trgm';
   3. как создать индекс
      1. в __table_args__ добавить index (см Item)
      2. в class добавить Search
      3. создать pydantic model <Name>ReadRelation содержащюю основную и вложенные модели по которым искать
      4. в repository.py: должен быть def get_query(cls, model: ModelType): с select с joinedload всех связей
      5. sh alembic.sh
   4. как проверить что поиск идет с триграммным индексом
      1. EXPLAIN ANALYZE 
         SELECT id FROM items 
         WHERE search_content ILIKE '%vin%';
      2. Если видишь Bitmap Heap Scan или Bitmap Index Scan с упоминанием idx_products_search_trgm — всё супер, 
      3. индекс работает. Если видишь Seq Scan — значит, база сканирует всю таблицу целиком. 
      4. Причина: либо в таблице слишком мало записей (до пары тысяч Postgres проще прочитать всё подряд), 
      5. либо подстрока поиска слишком короткая.
2. выполни 1 раз в postgresql

3. Как вообще устроен индекс: