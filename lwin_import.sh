#!/bin/bash
# Имя сервиса из docker-compose
SERVICE_NAME="test-wine_host-1"
# SERVICE_NAME="prod-wine_host-1"
DB_NAME="wine_db"
# Имя пользователя БД (замените, если отличается)
DB_USER="wine"
# Имя файла
# cat /путь/к/файлу.csv | docker exec -i имя_контейнера psql -U имя_пользователя -d имя_базы -c "\copy имя_таблицы FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER ';')"
# BACKUP_NAME="pg_backup_$(date +%Y%m%d_%H%M%S).sql"
FILE_NAME="upload_volume/LWINdatabase.txt"

echo "--- Начинаю импорт lwin в контейнер $SERVICE_NAME ---"

# Создаем дамп
cat $FILE_NAME | docker exec -i $SERVICE_NAME psql -U $DB_USER -d $DB_NAME -c "\copy lwins FROM STDIN WITH (FORMAT csv, HEADER true, DELIMITER E'\t')"

if [ $? -eq 0 ]; then
    echo "--- импорт успешно сделан ---"
else
    echo "Ошибка при создании импорта LWIN"
    exit 1
fi
