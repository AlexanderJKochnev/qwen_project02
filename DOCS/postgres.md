Выбор библиотеки: asyncpg vs psycopg (v3)
Характеристика
1. asyncpg	
2. psycopg (v3, async)
Производительность	
   1. Самая быстрая (использует собственный бинарный протокол).	
   2. Чуть медленнее (на 10-15%), но все равно очень быстрая.
Удобство	
   3. Специфичный синтаксис (аргументы через $1, $2).
   4. Стандартный DBAPI (аргументы через %s), более привычен.
Типы данных	
   5. Великолепная поддержка JSONB и массивов.	
   6. Лучшая поддержка сложных типов и расширений PostgreSQL.
Особенности	
   7. Не работает с PGBouncer в режиме "Transaction Mode" без костылей.	
   8. Отлично работает с PGBouncer и любыми прокси.

# useful tips
## копирование таблицы из одной базы Postgresql в другую (lwins переименовываем что бы не затереть во второй бд и копируем)
docker exec -i prod-wine_host-1 psql -U wine -d wine_db -c "
CREATE TABLE lwins2 AS SELECT * FROM lwins;"

docker exec -t prod-wine_host-1 pg_dump -U wine -t lwins2 wine_db | \
docker exec -i test-wine_host-1 psql -U wine wine_db