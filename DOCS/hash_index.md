## hash index
###  описание 

1. # посмотреть план запроса
docker compose exec -i wine_host psql -U wine -d wine_db -c "
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM items 
WHERE word_hashes && ARRAY[123456789, 987654321]::bigint[];
"
2. # проверить размер индекса
docker compose exec -i wine_host psql -U wine -d wine_db -c "
SELECT pg_size_pretty(pg_relation_size('idx_items_word_hashes_gin'));
"
3. # Статистика использования
docker compose exec -i wine_host psql -U wine -d wine_db -c "
SELECT idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes 
WHERE indexrelname = 'idx_items_word_hashes_gin';
"

4. # Обновление частот
docker compose exec -i wine_host psql -U wine -d wine_db -c "
-- Обнуляем старые частоты (которые были от hashtext)
UPDATE wordhashs SET freq = 0;
" 
docker compose exec -i wine_host psql -U wine -d wine_db -c "
-- Считаем вхождения правильных хешей из items
WITH df_counts AS (
    SELECT unnest(word_hashes) as h, count(*) as cnt
    FROM items
    GROUP BY h
)
UPDATE wordhashs w
SET freq = df.cnt
FROM df_counts df
WHERE w.hash = df.h;
"


docker compose exec -i wine_host psql -U wine -d wine_db -c "
docker compose exec -i wine_host psql -U wine -d wine_db -c "