# --- ЭТАП 1: Базовые зависимости (Base) ---
FROM ghcr.io/alexanderjkochnev/node:20-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
RUN apk add --no-cache certbot

# Stage 2: Раздача статики через Nginx
# FROM nginx:stable-alpine
FROM ghcr.io/alexanderjkochnev/nginx1.28.1:stable-alpine
# Копируем билд из первого стейджа
COPY --from=build-stage /app/dist /usr/share/nginx/html
# Копируем конфиг
COPY nginx.conf /etc/nginx/conf.d/default.conf

# ssl
# RUN apk add --no-cache certbot openssl
# RUN mkdir -p /var/www/certbot
# Создаем рабочие директории
# RUN mkdir -p /var/www/certbot /etc/letsencrypt /scripts
# Копируем скрипт в отдельную папку
# COPY entrypoint.sh /scripts/entrypoint.sh
#  RUN chmod +x /scripts/entrypoint.sh

# Папка для кэша nginx
RUN mkdir -p /var/cache/nginx

# Используем наш скрипт как основную точку входа
# ENTRYPOINT ["/scripts/entrypoint.sh"]

EXPOSE 80
# ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

