#!/bin/bash
SERVICE_NAME="test-wine_host-1"
DB_NAME="wine_db"
DB_USER="wine"
FILE_NAME="upload_volume/LWIN_clear.tsv"

# Список колонок строго в скобках
COLUMNS="(lwin, status, display_name, producer_title, producer_name, wine, country, region, sub_region, site, parcel, colour, type, sub_type, designation, classification, vintage_config, first_vintage, final_vintage, date_added, date_updated)"

echo "--- Начинаю импорт lwin в контейнер $SERVICE_NAME ---"

# 1. Устанавливаем формат даты
# 2. Запускаем \copy БЕЗ HEADER true (так как мы удалим заголовок сами)
# 3. Передаем данные через sed '1d' (удаление первой строки)
(echo "SET datestyle = 'ISO, DMY';"; \
 echo "\copy lwins $COLUMNS FROM STDIN WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '')"; \
 sed '1d; s/\r//g' "$FILE_NAME") | \
 docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME