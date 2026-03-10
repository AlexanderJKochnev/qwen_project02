#!/bin/bash
SERVICE_NAME="test-wine_host-1"
DB_NAME="wine_db"
DB_USER="wine"
FILE_NAME="upload_volume/LWIN_clear.tsv"

# Список колонок без ID
COLUMNS="(lwin, status, display_name, producer_title, producer_name, wine, country, region, sub_region, site, parcel, colour, type, sub_type, designation, classification, vintage_config, first_vintage, final_vintage, date_added, date_updated)"

echo "--- Начинаю импорт lwin в контейнер $SERVICE_NAME ---"

# 1. Сначала передаем настройку даты
# 2. Затем саму команду импорта с NULL ''
(echo "SET datestyle = 'ISO, DMY';"; \
 echo "\copy lwins $COLUMNS FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER E'\t', QUOTE E'\b', NULL '')"; \
 cat "$FILE_NAME" | sed 's/\r//g') | \
 docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME
