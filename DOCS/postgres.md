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

# список тааблиц с размерами
docker exec -i prod-wine_host-1 psql -U wine -d wine_db -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size
FROM pg_tables 
WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
# детльный отчет по таблице
docker exec -i prod-wine_host-1 psql -U wine -d wine_db -c "
SELECT 
    'Columns:' as info_type,
    column_name,
    data_type,
    null::text as index_info
FROM information_schema.columns 
WHERE table_name = 'producers'

UNION ALL

SELECT 
    'Indexes:',
    indexname,
    null,
    indexdef
FROM pg_indexes 
WHERE tablename = 'producers';
"
