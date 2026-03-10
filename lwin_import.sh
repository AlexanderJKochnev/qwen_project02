#!/bin/bash
# Имя сервиса из docker-compose
SERVICE_NAME="test-wine_host-1"
# SERVICE_NAME="prod-wine_host-1"
DB_NAME="wine_db"
# Имя пользователя БД (замените, если отличается)
DB_USER="wine"
# COLUMNS="(LWIN, STATUS, DISPLAY_NAME, PRODUCER_TITLE, PRODUCER_NAME, WINE, COUNTRY, REGION, SUB_REGION, SITE, PARCEL, COLOUR, TYPE, SUB_TYPE, DESIGNATION, CLASSIFICATION, VINTAGE_CONFIG, FIRST_VINTAGE, FINAL_VINTAGE, DATE_ADDED, DATE_UPDATED)"
COLUMNS="(lwin, status, display_name, producer_title, producer_name, wine, country, region, sub_region, site, parcel, colour, type, sub_type, designation, classification, vintage_config, first_vintage, final_vintage, date_added, date_updated)"
# Имя файла
# cat /путь/к/файлу.csv | docker exec -i имя_контейнера psql -U имя_пользователя -d имя_базы -c "\copy имя_таблицы FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ';')"
# BACKUP_NAME="pg_backup_$(date +%Y%m%d_%H%M%S).sql"
FILE_NAME="upload_volume/LWIN_clear.txt"

echo "--- Начинаю импорт lwin в контейнер $SERVICE_NAME ---"

# Создаем дамп
# cat $FILE_NAME | docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME -c "\copy lwins  FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER E'\t', QUOTE E'\b', NULL '')"

# cat $FILE_NAME | sed 's/\r//g' | docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME -c "\copy lwins $COLUMNS FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER E'\t', QUOTE E'\b', ENCODING 'WIN1251')"

cat $FILE_NAME | iconv -f cp1251 -t utf-8 | sed '1d; s/\r//g' | \
docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME \
-c "\copy lwins (lwin, status, display_name, producer_title, producer_name, wine, country, region, sub_region, site, parcel, colour, type, sub_type, designation, classification, vintage_config, first_vintage, final_vintage, date_added, date_updated) FROM STDIN WITH (FORMAT text, DELIMITER E'\t', ENCODING 'WIN1251')"


if [ $? -eq 0 ]; then
    echo "--- импорт успешно сделан ---"
else
    echo "Ошибка при создании импорта LWIN"
    exit 1
fi
