# как работает заполнение и обновление search_content в Items:
1. во всех зависимых моделях указан декоратор и путь к основной таблице
   1. @registers_search_update("drink_food.drink.item")
2. в случае изменения в таблице (create/get_or_create для Item и update/delete для зависимых от него) выполняется:
   1. CREATE: только для  Items: заполнение поля search_content (reindex_items) ДО сохранения в базу данных;
   2. PATCH/DELETE: 
      1. core.repository.sync_items_by_path (foods/varietals проверить)
      3. Заполнение полей через backgroundtasks[run_reindex_worker[fill_index]] (заменить на reindex_items?)
3. ручной запуск - router fill_index