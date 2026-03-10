#!/bin/bash
SERVICE_NAME="test-wine_host-1"
DB_NAME="wine_db"
DB_USER="wine"
FILE_NAME="upload_volume/LWIN_clear.tsv"

# Колонки для COPY (в порядке как в файле)
COLUMNS_COPY="(lwin, status, display_name, producer_title, producer_name, wine, country, region, sub_region, site, parcel, colour, type, sub_type, designation, classification, vintage_config, first_vintage, final_vintage, date_added, date_updated)"

# Колонки для INSERT (без скобок)
COL_NAMES="lwin, status, display_name, producer_title, producer_name, wine, country, region, sub_region, site, parcel, colour, type, sub_type, designation, classification, vintage_config, first_vintage, final_vintage, date_added, date_updated"

echo "--- 1. Создание временной таблицы lwins_temp ---"
docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME -c "
    DROP TABLE IF EXISTS lwins_temp;
    CREATE TABLE lwins_temp (
        lwin TEXT, status TEXT, display_name TEXT, producer_title TEXT,
        producer_name TEXT, wine TEXT, country TEXT, region TEXT,
        sub_region TEXT, site TEXT, parcel TEXT, colour TEXT,
        type TEXT, sub_type TEXT, designation TEXT, classification TEXT,
        vintage_config TEXT, first_vintage TEXT, final_vintage TEXT,
        date_added TEXT, date_updated TEXT
    );"

echo "--- 2. Загрузка данных из TSV (игнорируя ошибки типов) ---"
# Используем sed для удаления заголовка и символов \r
sed '1d; s/\r//g' "$FILE_NAME" | \
docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME \
-c "\copy lwins_temp $COLUMNS_COPY FROM STDIN WITH (FORMAT csv, DELIMITER E'\t', QUOTE E'\b', NULL '')"

echo "--- 3. Перенос данных в основную таблицу lwins с конвертацией ---"
docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME -c "
    INSERT INTO lwins ($COL_NAMES)
    SELECT
        NULLIF(lwin, '')::BIGINT,
        status, display_name, producer_title, producer_name, wine, country, region, sub_region, site, parcel, colour, type, sub_type, designation, classification, vintage_config, first_vintage, final_vintage,
        -- Обработка даты: если формат совпадает, конвертируем, иначе NULL
        CASE
            WHEN date_added ~ '^\d{2}\.\d{2}\.\d{4}' THEN to_timestamp(date_added, 'DD.MM.YYYY HH24:MI')
            ELSE NULL
        END,
        CASE
            WHEN date_updated ~ '^\d{2}\.\d{2}\.\d{4}' THEN to_timestamp(date_updated, 'DD.MM.YYYY HH24:MI')
            ELSE NULL
        END
    FROM lwins_temp;

    DROP TABLE lwins_temp;
"

echo "--- Готово! Проверка количества строк: ---"
docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME -c "SELECT count(*) FROM lwins;"
