#!/bin/bash
# Имя сервиса из docker-compose
SERVICE_NAME="wine_host"
# Имя пользователя БД (замените, если отличается)
DB_USER="wine"
# Имя файла бэкапа
# BACKUP_NAME="pg_backup_$(date +%Y%m%d_%H%M%S).sql"
BACKUP_NAME="pg_backup.sql.gz"

echo "--- Начинаю бэкап базы данных из контейнера $SERVICE_NAME ---"

# Создаем дамп
docker exec -t $SERVICE_NAME pg_dumpall -c -U $DB_USER | gzip > "backup/$BACKUP_NAME"

if [ $? -eq 0 ]; then
    echo "--- Бэкап POSTGRESQL успешно создан: $BACKUP_NAME ---"
    echo "Теперь можно останавливать контейнеры и удалять папку pg_data."
else
    echo "Ошибка при создании бэкапа POSTGRESQL"
    exit 1
fi
