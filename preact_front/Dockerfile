# --- ЭТАП 1: Базовые зависимости (Base) ---
# FROM ghcr.io/alexanderjkochnev/node:20-alpine AS build-stage
FROM node:local AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
RUN apk add --no-cache certbot

# Stage 2: Раздача статики через Nginx
# FROM ghcr.io/alexanderjkochnev/nginx1.28.1:stable-alpine
FROM nginx:local

# Устанавливаем envsubst для замены переменных (НОВОЕ)
RUN apk add --no-cache gettext

# Копируем билд из первого стейджа
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Копируем конфиг
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем entrypoint скрипт (НОВОЕ)
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Папка для кэша nginx
RUN mkdir -p /var/cache/nginx

EXPOSE 80

# Меняем entrypoint (НОВОЕ)
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]

