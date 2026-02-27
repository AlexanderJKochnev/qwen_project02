#!/bin/sh
# preact_front/docker-entrypoint.sh

set -e

echo "========================================="
echo "Preact Frontend Entrypoint"
echo "========================================="

# Значение по умолчанию
DEFAULT_API_URL="https://api.abc8888.ru"

# Берем URL из переменной окружения или используем дефолт
API_URL="${VITE_API_URL:-$DEFAULT_API_URL}"

echo "Setting API URL to: $API_URL"

# Заменяем конфигурацию в index.html
# Ищем блок с __RUNTIME_CONFIG__ и заменяем URL
sed -i.bak \
    "s|window\.__RUNTIME_CONFIG__\s*=\s*{[^}]*};|window.__RUNTIME_CONFIG__ = { API_URL: '${API_URL}' };|g" \
    /usr/share/nginx/html/index.html

# Удаляем бэкап
rm -f /usr/share/nginx/html/index.html.bak

# Проверяем результат
echo "========================================="
echo "Final index.html config:"
grep -A 2 "__RUNTIME_CONFIG__" /usr/share/nginx/html/index.html || echo "Config not found!"
echo "========================================="

# Запускаем nginx
exec "$@"