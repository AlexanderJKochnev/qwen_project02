#!/bin/bash

# --- НАСТРОЙКИ ---
HDD_BASE="/mnt/hdd_data/projects"
PROJECT_NAME=$(basename "$PWD")
TARGET_DIR="$HDD_BASE/$PROJECT_NAME"

if [ "$(id -u)" -ne 0 ]; then echo "Запустите от sudo"; exit 1; fi

echo "--- Анализ проекта: $PROJECT_NAME ---"

# 1. Извлекаем ТОЛЬКО локальные тома из секции volumes через yq
volumes=$(yq eval '.services[].volumes[]' docker-compose*.yaml 2>/dev/null | \
          cut -d':' -f1 | grep '^\./' | sed "s/['\"]//g" | sort -u)

if [ -z "$volumes" ]; then
    echo "В секциях volumes: локальных путей (./) не обнаружено."
    exit 0
fi

# 2. Вывод списка и запрос подтверждения
echo "Найдены следующие тома для переноса на HDD:"
printf '%s\n' "$volumes" | sed 's/^/  [ ] /'
echo "------------------------------------------"
read -p "Монтировать эти тома на HDD? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Операция отменена пользователем."
    exit 0
fi

# 3. ОЧИСТКА ПЕРЕД МОНТИРОВАНИЕМ (защита от дублей)
echo "Очистка старых записей для этого проекта..."
umount -l "$PWD"/* 2>/dev/null
sed -i "\|$PWD|d" /etc/fstab

# 4. ОБРАБОТКА ТОМОВ
mkdir -p "$TARGET_DIR"

for vol in $volumes; do
    vol_clean=$(echo "$vol" | sed 's|^\./||')
    src_path="$PWD/$vol_clean"
    dst_path="$TARGET_DIR/$vol_clean"

    echo "Настройка: $vol_clean"

    mkdir -p "$src_path"
    mkdir -p "$dst_path"

    # Перенос данных (если на SSD есть, а на HDD пусто)
    if [ "$(ls -A "$src_path" 2>/dev/null)" ] && [ ! "$(ls -A "$dst_path" 2>/dev/null)" ]; then
        echo "  [>] Перенос данных на HDD..."
        rsync -a "$src_path/" "$dst_path/"
        find "$src_path" -mindepth 1 -delete
    fi

    # Добавляем в fstab (Bind Mount)
    echo "$dst_path $src_path none defaults,bind,nofail,x-systemd.requires=/mnt/hdd_data 0 0" >> /etc/fstab
done

# 5. ПРИМЕНЕНИЕ
systemctl daemon-reload
mount -a

echo "--- ГОТОВО ---"
findmnt -R "$PWD"
