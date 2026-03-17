#!/bin/bash
#
SERVICE_NAME="test-wine_host-1"
# SERVICE_NAME="prod-wine_host-1"

# удаляем битые записи
docker exec $SERVICE_NAME psql -U wine -d wine_db -c "
DELETE FROM lwins WHERE producer_name = 'test'"
# вставляем записи в region
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "
INSERT INTO producertitles (name)
SELECT DISTINCT producer_title FROM lwins
WHERE producer_title IS NOT NULL AND producer_title <> ''
ON CONFLICT (name) DO NOTHING;"
# проверяем
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "SELECT id, name FROM producertitles"

docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "
INSERT INTO producers (name, producertitle_id)
SELECT DISTINCT ON (l.producer_name) l.producer_name, s.id
FROM lwins l
JOIN producertitles s ON l.producer_title = s.name
WHERE l.producer_name IS NOT NULL AND l.producer_name <> '';"

docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "
INSERT INTO producers (name, producertitle_id)
SELECT DISTINCT ON (l.producer_name) l.producer_name, l.wine
FROM lwins l
WHERE l.producer_name IS NOT NULL AND l.producer_name <> '' AND producer_title IS NULL;
"

# docker exec -i test-wine_host-1 psql -U wine -d wine_db -c ""