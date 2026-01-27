### MEILISEARCH ПОИСК ###
1. Проверка наличия индекса
   1. Создание индекса если его нет
      1. Заполнение индекса
2. Meilisearch index maintaing:
   1. app/support/outbox/service/sync_with_meilisearch: 
      1. этот декоратор вешается на любой сервисный метод изменяющий записи.
      2. не делай это с app/core/service/Service, только через app/support иначе этот поиск будет по всем моделям, а это излишне
      3. оптимально Item, parser.Rawdata, может быть Drink
   2. Все изменения пишутся в Outbox (postgresql)
   3. dd
   4. 
