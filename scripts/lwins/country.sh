#!/bin/bash
#
SERVICE_NAME="test-wine_host-1"
# SERVICE_NAME="prod-wine_host-1"

# удаляем битые записи
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "SELECT DISTINCT l.region, c.id
FROM lwins l JOIN countries c ON l.country = c.name WHERE l.region IS NOT NULL AND l.region <> ''"
# вставляем записи в country
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "INSERT INTO countries (name) SELECT DISTINCT country
FROM lwins WHERE country IS NOT NULL AND country <> '' ON CONFLICT (name) DO NOTHING;"
# проверяем
docker exec -i $SERVICE_NAME psql -U wine -d wine_db -c "SELECT id, name FROM countries"

# docker exec test-wine_host-1 psql -U wine -d wine_db -c "INSERT INTO countries (name) SELECT DISTINCT country FROM lwins WHERE country IS NOT NULL AND country <> '' ON CONFLICT (name) DO NOTHING;"
# docker exec test-wine_host-1 psql -U wine -d wine_db -c "SELECT id, name FROM countries"