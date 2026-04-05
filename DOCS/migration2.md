# DOCS/migration2.md
## миграция на именованные тома btrfs
# 1. Создаем подтом
sudo btrfs subvolume create /mnt/hdd_data/@named_volumes

# 2. Отключаем CoW (рекурсивно для всех будущих файлов)
sudo chattr +C /mnt/hdd_data/@named_volumes

# Проверяем (должна быть буква C)
lsattr -d /mnt/hdd_data/@named_volumes
