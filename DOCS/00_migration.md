## ТУТ ПРИВОДИТСЯ ОСОБЫЙ ПОРЯЛДОК ИМЛЕМЕНТАЦИИ ИЗМЕНЕНИЙ В PRODUCTION ПОСЛЕ ТЕСТИРОВАНИЯ
### после выполнения - если эти действия носят разовый характер - обнулить текст ниже
#### если нет - внести в постоянную  инструкцию или сделать автоматизацию и 

# ПЕРЕХОД ОТ FTS НА ХЭШ ИНДЕКС
1. после обновления git и запуска сделать sh.alembic.sh, затем dump test, restore wine

# ПОИСК ДУБЛИКАТОВ В ITEMS/DRINKS ПО ХЭШ ИНДЕКСУ
выполняется в clickhouse 

-- Проверяем для одного вина из группы 1 (например, id = 123)
WITH reference AS (
    SELECT word_hashes
    FROM wine_replica.items i
    JOIN wine_replica.drinks d ON i.drink_id = d.id
    WHERE d.id = 123  -- id вина из группы 1 (lwin = None)
    LIMIT 1
)
SELECT 
    d.id,
    d.title,
    d.lwin,
    round(
        length(arrayIntersect(i.word_hashes, (SELECT word_hashes FROM reference))) / 
        length((SELECT word_hashes FROM reference)),
        7
    ) as similarity
FROM wine_replica.drinks d
JOIN wine_replica.items i ON i.drink_id = d.id
WHERE d.lwin IS NOT NULL
    AND hasAny(i.word_hashes, (SELECT word_hashes FROM reference))
ORDER BY similarity DESC, length(i.word_hashes), id 
LIMIT 20;

