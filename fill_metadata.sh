#!/bin/bash
# создание trigram-indexes
# Определяем путь к директории скрипта
# YНЕ НУЖЕН
docker exec -i wine_host psql -U wine -d wine_db < scripts/jsonb_raw.sql

docker exec -i wine_host psql -U wine -d wine_db -c "UPDATE rawdatas SET metadata_json = parsed_data::jsonb;"
