"""
проверка перед настройкой уникального индекса unaccent
(нижний регистр, преобразованы диакритические знаки в латиницу"
"""
varietals ok
foods ok
categories ok
countries ok
drinks
items
parcels ok
sites   ok
producers ok
producertitles ok
regions ok
subregions ok
subcategory ok


vintages



(далее на примере foods)

docker compose exec -i wine_host psql -U wine -d wine_db -c "
CREATE EXTENSION IF NOT EXISTS unaccent;
SELECT unaccent(lower(name)) AS normalized_value, COUNT(*) 
FROM foods 
GROUP BY 1 
HAVING COUNT(*) > 1;"

docker compose exec -i wine_host psql -U wine -d wine_db -c "
BEGIN;

-- 1. Создаем временную таблицу дубликатов
CREATE TEMP TABLE food_duplicates AS
WITH ranked_foods AS (
    SELECT 
        id,
        unaccent(lower(name)) as normalized_name,
        MIN(id) OVER(PARTITION BY unaccent(lower(name))) as keeper_id
    FROM foods
)
SELECT id, keeper_id 
FROM ranked_foods 
WHERE id != keeper_id;

-- 2. Удаляем из связей те дубликаты, которые привели бы к созданию точных копий (drink_id, keeper_id)
-- Это защищает от дублирования строк в ассоциативной таблице
DELETE FROM drink_food_associations dfa
USING food_duplicates fd
WHERE dfa.food_id = fd.id
  AND EXISTS (
      SELECT 1 
      FROM drink_food_associations dfa2 
      WHERE dfa2.drink_id = dfa.drink_id 
        AND dfa2.food_id = fd.keeper_id
  );

-- 3. Теперь безопасно обновляем оставшиеся ссылки на правильный ID (keeper_id)
UPDATE drink_food_associations dfa
SET food_id = fd.keeper_id
FROM food_duplicates fd
WHERE dfa.food_id = fd.id;

-- 4. Удаляем дубликаты из основной таблицы foods
DELETE FROM foods
WHERE id IN (SELECT id FROM food_duplicates);

DROP TABLE food_duplicates;

COMMIT;
"

# для составного индекса 
docker compose exec -i wine_host psql -U wine -d wine_db -c "
BEGIN;

-- 1. Вычисляем дубликаты подрегионов
CREATE TEMP TABLE subregion_duplicates AS
WITH ranked_subregions AS (
    SELECT 
        id,
        region_id,
        unaccent(lower(name)) as normalized_name,
        MIN(id) OVER(PARTITION BY region_id, unaccent(lower(name))) as keeper_id
    FROM subregions
)
SELECT id, keeper_id 
FROM ranked_subregions 
WHERE id != keeper_id;

-- 2. Находим сайты, которые привязаны к дубликатам подрегионов.
-- Нам нужно понять, какой сайт сделать главным (keeper_site_id) для одинаковых подрегионов.
CREATE TEMP TABLE site_mapping AS
WITH ranked_sites AS (
    SELECT 
        s.id AS old_site_id,
        (
            SELECT s2.id 
            FROM sites s2 
            WHERE s2.subregion_id = sd.keeper_id 
            LIMIT 1
        ) AS keeper_site_id
    FROM sites s
    JOIN subregion_duplicates sd ON s.subregion_id = sd.id
)
SELECT old_site_id, keeper_site_id 
FROM ranked_sites 
WHERE keeper_site_id IS NOT NULL AND old_site_id != keeper_site_id;

-- 3. САМЫЙ ВАЖНЫЙ ШАГ: Перевешиваем напитки (drinks) на 'выжившие' сайты
-- Теперь foreign key не будет ругаться, так как у старых сайтов не останется зависимостей
UPDATE drinks d
SET site_id = sm.keeper_site_id
FROM site_mapping sm
WHERE d.site_id = sm.old_site_id;

-- 4. Теперь старые сайты свободны от связей с drinks, их можно безопасно удалить
DELETE FROM sites
WHERE id IN (SELECT old_site_id FROM site_mapping);

-- 5. Переводим оставшиеся сайты (у которых не было сайтов-близнецов) на правильные ID подрегионов
UPDATE sites s
SET subregion_id = sd.keeper_id
FROM subregion_duplicates sd
WHERE s.subregion_id = sd.id;

-- 6. Удаляем дубликаты из основной таблицы subregions
DELETE FROM subregions
WHERE id IN (SELECT id FROM subregion_duplicates);

DROP TABLE site_mapping;
DROP TABLE subregion_duplicates;

COMMIT;
"
#=====regions=============
docker compose exec -i wine_host psql -U wine -d wine_db -c "
BEGIN;

-- 1. подставляем дубликаты
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE TEMP TABLE region_duplicates AS
WITH ranked_regions AS (
    SELECT 
        id,
        unaccent(lower(name)) as normalized_name,
        MIN(id) OVER(PARTITION BY country_id, unaccent(lower(name))) as keeper_id
    FROM regions
)
SELECT id, keeper_id 
FROM ranked_regions 
WHERE id != keeper_id;

-- 2. Карта соответствия подрегионов: связываем подрегионы из дублирующих регионов 
-- с подрегионами из 'выживших' регионов (по их нормализованному имени)
CREATE TEMP TABLE subregion_mapping AS
WITH mapped_subregions AS (
    SELECT 
        s_old.id AS old_subregion_id,
        s_keeper.id AS keeper_subregion_id
    FROM subregions s_old
    JOIN region_duplicates rd ON s_old.region_id = rd.id
    JOIN subregions s_keeper ON s_keeper.region_id = rd.keeper_id 
         AND coalesce(unaccent(lower(s_keeper.name)),'none') = coalesce(unaccent(lower(s_old.name)), 'none')
)
SELECT old_subregion_id, keeper_subregion_id 
FROM mapped_subregions
WHERE old_subregion_id != keeper_subregion_id;

-- 3. Карта соответствия сайтов: находим сайты, привязанные к старым подрегионам
CREATE TEMP TABLE site_mapping AS
WITH mapped_sites AS (
    SELECT 
        s_old.id AS old_site_id,
        (
            SELECT s_keeper.id 
            FROM sites s_keeper 
            WHERE s_keeper.subregion_id = sm.keeper_subregion_id 
            LIMIT 1
        ) AS keeper_site_id
    FROM sites s_old
    JOIN subregion_mapping sm ON s_old.subregion_id = sm.old_subregion_id
)
SELECT old_site_id, keeper_site_id 
FROM mapped_sites
WHERE keeper_site_id IS NOT NULL AND old_site_id != keeper_site_id;

-- 4. ПЕРЕНОС ДАННЫХ: Перевешиваем напитки (drinks) на 'выжившие' сайты
UPDATE drinks d
SET site_id = sim.keeper_site_id
FROM site_mapping sim
WHERE d.site_id = sim.old_site_id;

-- 5. Удаляем старые сайты, которые теперь освободились от foreign key ограничений
DELETE FROM sites
WHERE id IN (SELECT old_site_id FROM site_mapping);

-- 6. Переводим оставшиеся сайты (у которых не было сайтов-близнецов) на правильные подрегионы
UPDATE sites s
SET subregion_id = sm.keeper_subregion_id
FROM subregion_mapping sm
WHERE s.subregion_id = sm.old_subregion_id;

-- 7. Теперь старые подрегионы свободны от связей с таблицей sites, удаляем их
DELETE FROM subregions
WHERE id IN (SELECT old_subregion_id FROM subregion_mapping);

-- 8. Если остались подрегионы в удаляемых регионах, которые были уникальными 
-- (их имя не дублировалось в новом регионе), просто переносим их в новый регион
UPDATE subregions s
SET region_id = rd.keeper_id
FROM region_duplicates rd
WHERE s.region_id = rd.id;

-- 9. ФИНАЛ: Удаляем дубликаты из основной таблицы regions
DELETE FROM regions
WHERE id IN (SELECT id FROM region_duplicates);

-- Очистка временных структур
DROP TABLE site_mapping;
DROP TABLE subregion_mapping;
DROP TABLE region_duplicates;

COMMIT;
"