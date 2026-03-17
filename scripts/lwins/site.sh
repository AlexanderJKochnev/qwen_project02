#!/bin/bash
#
SERVICE_NAME="test-wine_host-1"
# SERVICE_NAME="prod-wine_host-1"

# удаляем битые записи
# docker exec $SERVICE_NAME psql -U wine -d wine_db -c "SELECT DISTINCT l.region, c.id FROM lwins l JOIN countries c ON l.country = c.name WHERE l.region IS NOT NULL AND l.region <> ''"
# вставляем записи в region
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "INSERT INTO sites (name, subregion_id)
SELECT DISTINCT ON (l.site) l.site, s.id
FROM lwins l
JOIN subregions s ON l.sub_region = s.name
WHERE l.site IS NOT NULL AND l.site <> ''
ON CONFLICT (name, subregion_id) DO NOTHING;"
# проверяем
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "SELECT id, name FROM sites"
