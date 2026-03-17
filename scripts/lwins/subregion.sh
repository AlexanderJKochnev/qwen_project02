#!/bin/bash
#
SERVICE_NAME="test-wine_host-1"
# SERVICE_NAME="prod-wine_host-1"

# удаляем битые записи
# docker exec $SERVICE_NAME psql -U wine -d wine_db -c "SELECT DISTINCT l.region, c.id FROM lwins l JOIN countries c ON l.country = c.name WHERE l.region IS NOT NULL AND l.region <> ''"
# вставляем записи в region
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "INSERT INTO subregions (name, region_id)
SELECT DISTINCT ON (l.sub_region) l.sub_region, r.id
FROM lwins l
JOIN regions r ON l.region = r.name
WHERE l.sub_region IS NOT NULL AND l.sub_region <> ''
ON CONFLICT (name) DO NOTHING;"
# проверяем
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "SELECT id, name FROM subregions"
