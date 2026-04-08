#!/bin/bash
# Имя сервиса из docker-compose
SERVICE_NAME="prod-wine_host-1"
# Имя пользователя БД
DB_USER="wine"
# Имя файла бэкапа
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
