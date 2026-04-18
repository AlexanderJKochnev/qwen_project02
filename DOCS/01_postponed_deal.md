## ОТЛОЖЕННЫЕ ДОРАБОТКИ.
1. ЗАМЕНА ИНДЕКСА FTS на HASH
   1. item.serv ice.run_reindex_worker:
      1. удалить item.search_content = content.lower()
   2. app.core.utils.reindexation
      1. удалить instance.search_content = raw_text.lower()
   3. app/core/models/base_model
      1. class Search - удалить все кроме word_hashes...
   4. app/core/repositories/sqlalchemy_repository.py
      1. sync_items_by_path  # cюда нужно добавить обновление wordhash
      2. 
2. Error: HTTP 500: {"detail":"ReadRouter, countries: 'dict' object has no attribute 'to_dict'"}