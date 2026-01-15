#!/bin/bash
# Имя сервиса из docker-compose
SERVICE_NAME="wine_db"
# Имя пользователя БД (замените, если отличается)
DB_USER="postgres"
# Имя файла бэкапа
BACKUP_NAME="pg_backup_$(date +%Y%m%d_%H%M%S).sql"

echo "--- Начинаю бэкап базы данных из контейнера $SERVICE_NAME ---"

# Создаем дамп
docker-compose exec -T $SERVICE_NAME pg_dumpall -U $DB_USER > "$BACKUP_NAME"

if [ $? -eq 0 ]; then
    echo "--- Бэкап успешно создан: $BACKUP_NAME ---"
    echo "Теперь можно останавливать контейнеры и удалять папку pg_data."
else
    echo "Ошибка при создании бэкапа!"
    exit 1
fi
