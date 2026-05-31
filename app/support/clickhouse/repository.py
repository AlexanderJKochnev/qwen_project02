# app/support/clickhouse/repository.py

"""

"""
# varietals
"""
SELECT
    v_ch.id AS ch_id,
    v_ch.name AS new_varietal_name
FROM default.pg_varietal AS v_ch
LEFT JOIN (
    -- Выбираем актуальные записи из Postgres, отсекая дубли модификатором FINAL
    SELECT id, name
    FROM drink_replica.varietals FINAL
) AS v_pg
    ON lower(trimBoth(v_ch.name)) = lower(trimBoth(v_pg.name))
-- Оставляем только те строки, которые не нашли совпадения в Postgres
WHERE (v_pg.name = '' OR v_pg.name IS NULL)
AND new_varietal_name NOT LIKE '$%';
"""
# foods
"""
SELECT
    v_ch.id AS ch_id,
    v_ch.name AS new_food_name
FROM default.pg_food AS v_ch
LEFT JOIN (
    -- Выбираем актуальные записи из Postgres, отсекая дубли модификатором FINAL
    SELECT id, name
    FROM drink_replica.foods FINAL
) AS v_pg
    ON lower(trimBoth(v_ch.name)) = lower(trimBoth(v_pg.name))
-- Оставляем только те строки, которые не нашли совпадения в Postgres
WHERE (v_pg.name = '' OR v_pg.name IS NULL)
"""
# country
# 4. Buy Now
# 6. DrizlyVivino
"""
SELECT
    v_ch.id AS ch_id,
    v_ch.name AS new_name
FROM default.pg_country AS v_ch
LEFT JOIN (
    -- Выбираем актуальные записи из Postgres, отсекая дубли модификатором FINAL
    SELECT id, name
    FROM drink_replica.countries FINAL
) AS v_pg
    ON lower(trimBoth(v_ch.name)) = lower(trimBoth(v_pg.name))
-- Оставляем только те строки, которые не нашли совпадения в Postgres
WHERE (v_pg.name = '' OR v_pg.name IS NULL)
AND new_name NOT LIKE 'US%';
"""
# region
"""
SELECT
    v_ch.id AS ch_id,
    v_ch.name AS new_name
FROM default.pg_region AS v_ch
LEFT JOIN (
    -- Выбираем актуальные записи из Postgres, отсекая дубли модификатором FINAL
    SELECT id, name
    FROM drink_replica.regions FINAL
) AS v_pg
    ON lower(trimBoth(v_ch.name)) = lower(trimBoth(v_pg.name))
-- Оставляем только те строки, которые не нашли совпадения в Postgres
WHERE (v_pg.name = '' OR v_pg.name IS NULL)
AND new_name NOT LIKE '$%';
"""
# subregion
"""

"""