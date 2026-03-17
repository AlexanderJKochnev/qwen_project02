#!/bin/bash
#
SERVICE_NAME="test-wine_host-1"
# SERVICE_NAME="prod-wine_host-1"

# удаляем битые записи
# docker exec $SERVICE_NAME psql -U wine -d wine_db -c "SELECT DISTINCT l.region, c.id FROM lwins l JOIN countries c ON l.country = c.name WHERE l.region IS NOT NULL AND l.region <> ''"
# вставляем записи в region
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "
INSERT INTO producertitles (name)
SELECT DISTINCT producer_title FROM lwins
WHERE producer_title IS NOT NULL AND producer_title <> ''
ON CONFLICT (name) DO NOTHING;"
# проверяем
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "SELECT id, name FROM producertitles"

# docker exec -i test-wine_host-1 psql -U wine -d wine_db -c ""