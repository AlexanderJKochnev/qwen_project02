#!/bin/bash

# Скрипт для создания суперпользователя в Django и FastAPI
# Проверяет существование пользователя, но продолжает для второй системы
# НЕ НУЖЕН - ИСПОЛЬЗУЙ createsuper.sh

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

# Функция: проверка, существует ли пользователь в Django по email
django_user_exists() {
    local email="$1"
    local result
    result=$(docker compose exec -T django python -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
print('1' if User.objects.filter(email='$email').exists() else '0')
" 2>/dev/null) || return 1
    [[ "$result" == "1" ]]
}

# Функция: создание в Django (с проверкой)
create_django_superuser() {
    local username="$1"
    local email="$2"
    local password="$3"

    if [ -n "$username" ] && [ -n "$email" ] && [ -n "$password" ]; then
        echo "🔄 Проверка существования пользователя в Django Admin..."
        if django_user_exists "$email"; then
            echo "⚠️  Пользователь с email '$email' уже существует в Django. Пропуск создания."
        else
            echo "✅ Создаём суперпользователя в Django Admin..."
            docker compose exec -T django python manage.py createsuperuser --noinput --username "$username" --email "$email" --skip-checks
            # Устанавливаем пароль
            docker compose exec -T django python -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(email='$email')
u.set_password('$password')
u.save()
print('Пароль установлен.')
"
            echo "✅ Суперпользователь '$username' создан в Django Admin."
        fi
    else
        echo "✅ Интерактивное создание в Django Admin..."
        docker compose exec django python manage.py createsuperuser
    fi
}

# Функция: проверка, существует ли пользователь в FastAPI по email
fastapi_user_exists() {
    local email="$1"
    local result
    result=$(docker compose exec -T app python -c "
import asyncio
import sys
sys.path.append('/app')
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.core.models.user import User  # ← Замените на путь к вашей модели User

async def check():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == '$email'))
        user = result.scalar_one_or_none()
        print('1' if user else '0')

asyncio.run(check())
" 2>/dev/null) || return 1
    [[ "$result" == "1" ]]
}

# Функция: создание в FastAPI (с проверкой)
create_fastapi_superuser() {
    local username="$1"
    local email="$2"
    local password="$3"

    if [ -n "$username" ] && [ -n "$email" ] && [ -n "$password" ]; then
        echo "🔄 Проверка существования пользователя в FastAPI..."
        if fastapi_user_exists "$email"; then
            echo "⚠️  Пользователь с email '$email' уже существует в FastAPI. Пропуск создания."
        else
            echo "✅ Создаём суперпользователя в FastAPI..."
            docker compose exec -T app python -m app.admin.create_superuser "$username" "$email" "$password"
        fi
    else
        echo "✅ Интерактивное создание в FastAPI..."
        docker compose exec -it app python -m app.admin.create_superuser
    fi
}

# Основная логика
if [ $# -eq 3 ]; then
    username="$1"
    email="$2"
    password="$3"
    echo "🚀 Создание суперпользователя в Django и FastAPI..."
    create_django_superuser "$username" "$email" "$password"
    create_fastapi_superuser "$username" "$email" "$password"
elif [ "$1" = "--interactive" ]; then
    echo "🚀 Интерактивное создание суперпользователя..."
    create_django_superuser
    create_fastapi_superuser
else
    echo "🚀 Интерактивное создание суперпользователя..."
    create_django_superuser
    create_fastapi_superuser
fi

echo "✅ Процесс создания суперпользователя завершён."