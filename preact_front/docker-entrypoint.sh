#!/bin/sh
# preact_front/docker-entrypoint.sh
set -e

echo "========================================="
echo "Preact Frontend Entrypoint"
echo "========================================="

DEFAULT_API_URL="https://api.abc8888.ru"
API_URL="${VITE_API_URL:-$DEFAULT_API_URL}"
echo "Setting API URL to: $API_URL"

# Просто заменяем URL в строке с API_URL
sed -i "s|https://api.abc8888.ru|${API_URL}|g" /usr/share/nginx/html/index.html

# Проверяем результат
echo "========================================="
echo "Final index.html config:"
grep -A 2 "__RUNTIME_CONFIG__" /usr/share/nginx/html/index.html || echo "Config not found!"
echo "========================================="

exec "$@"