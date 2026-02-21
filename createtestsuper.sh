#!/bin/bash

# Скрипт для создания суперпользователя

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Использование:"
    echo "  $0                    # Интерактивное создание"
    echo "  $0 --interactive      # Интерактивное создание"
    echo "  $0 username email password  # Создание с параметрами"
    echo ""
    echo "Примеры:"
    echo "  $0"
    echo "  $0 admin admin@example.com mypassword"
    exit 0
fi

# Проверяем, переданы ли аргументы
if [ $# -eq 3 ]; then
    echo "Создание суперпользователя с параметрами..."
    docker compose -f docker-compose.test.yaml exec app python -m app.admin.create_superuser "$1" "$2" "$3"
elif [ "$1" = "--interactive" ]; then
    echo "Интерактивное создание суперпользователя..."
    docker compose docker-compose.test.yaml exec -it app python -m app.admin.create_superuser --interactive
else
    echo "Интерактивное создание суперпользователя..."
    docker compose docker-compose.test.yaml exec -it app python -m app.admin.create_superuser
fi