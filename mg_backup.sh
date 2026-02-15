#!/bin/bash
# Имя сервиса из docker-compose
SERVICE_NAME="mongo"
HOST="mongodb"
PORT="27017"
USERNAME="admin"
PASSWORD="admin"
BACKUP_NAME="mg_backup.gz"

echo "--- Начинаю бэкап базы данных из контейнера $SERVICE_NAME ---"
docker exec -t $SERVICE_NAME mongodump --host=mongo \
                               --port=27017 \
                               --username=admin \
                               --password='admin' \
                               --authenticationDatabase=admin \
                               --archive \
                               --gzip > backup/$BACKUP_NAME
# docker exec -t mongo mongodump --help
# docker-compose exec -t $SERVICE_NAME pg_dumpall -c -U $DB_USER > "backup/$BACKUP_NAME"

if [ $? -eq 0 ]; then
    echo "--- Бэкап MONGODB успешно создан: $BACKUP_NAME ---"
else
    echo "Ошибка при создании бэкапа MONGODB"
    exit 1
fi
