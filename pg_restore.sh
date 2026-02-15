#!/bin/bash
# Имя сервиса из docker-compose
SERVICE_NAME="wine_host"
# Имя пользователя БД (замените, если отличается)
DB_USER="wine"
# Имя файла бэкапа
# BACKUP_NAME="pg_backup_$(date +%Y%m%d_%H%M%S).sql"
BACKUP_NAME="pg_backup.sql"

echo "--- Начинаю восстановление базы данных из контейнера $SERVICE_NAME ---"

cat backup/$BACKUP_NAME | docker exec -i $SERVICE_NAME psql -U $DB_USER -d postgres

if [ $? -eq 0 ]; then
    echo "--- база данных POSTGRESQL успешно восстановлена из $BACKUP_NAME ---"
else
    echo "Ошибка при восстановления бэкапа POSTGRESQL из $BACKUP_NAME"
    exit 1
fi
