### MEILISEARCH ПОИСК ###
1. Проверка наличия индекса
   1. Создание индекса если его нет
      1. Заполнение индекса
2. Meilisearch index maintaing:
   1. .env MEILISEARCH - добавь сюда название модели в которой должен происходить поиск
   2. проверь наличие pydantic схемы <model_name>ReadRelation - по ней происходит  поиск на всю глубину
   3. app.core.service/service.py::_queue_meili_sync
      1. записывает в очередь данные для индексации 
      2. очередь хранится в app/support/outbox/outbox_model.py::MeiliOutbox
   5. 
   6. 
