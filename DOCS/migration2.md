# DOCS/migration2.md
## миграция на именованные тома btrfs
# 1. Создаем подтом
sudo btrfs subvolume create /mnt/hdd_data/@named_volumes

# 2. Отключаем CoW (рекурсивно для всех будущих файлов)
sudo chattr +C /mnt/hdd_data/@named_volumes

# 3. Проверяем (должна быть буква C)
lsattr -d /mnt/hdd_data/@named_volumes

# 4. Создаем директорию для bind

# 5. В .env устанавливаем переменную
BIND_VOLUMES=/mnt/hdd_data/@named_volumes

# 6. В docker-compose.yaml указаываем пути в секции volume:
    volumes:
      - ${BIND_VOLUMES}/${COMPOSE_PROJECT_NAME}_pg_data:/var/lib/postgresql/data
# 7. Для Postgresql, mongodb - восстанавливаем через dump