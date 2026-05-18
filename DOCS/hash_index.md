## hash index
###  описание DEPERECATED
1. Получение всех текстовых данных записи. 
   1. app.core.repositories.repo_backround_tasks.Background.extract_text_optimized
2. Разбивка на токены. Удаление мусора первый этап. 
   1. app.core.hash_norm.get_word_hashes_dict   :: ВОТ ОТСЮДА
      1. Разбивка на токены/удаление мусора :: app.core.hash_norm.tokenize
      2. Получение основных форм :: app.core.utils.morphology3.get_lemma
      3. Определение лидера синонимов :: app.core.utils.morphology3.get_synonym_leader
      4. Получение хэша :: app.core.hash_norm.get_cached_hash








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
