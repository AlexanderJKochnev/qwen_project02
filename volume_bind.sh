#!/bin/bash

# --- НАСТРОЙКИ --- монтирует binding volumes ! запускать строго перед первым запуском docker-compose
HDD_BASE="/mnt/hdd_data/projects"
PROJECT_NAME=$(basename "$PWD")
TARGET_DIR="$HDD_BASE/$PROJECT_NAME"

if [[ $EUID -ne 0 ]]; then echo "Запустите от sudo"; exit 1; fi

echo "--- Настройка проекта: $PROJECT_NAME ---"

# 1. Сбор всех уникальных путей томов из всех compose файлов
# Ищем строки вида "./data:/var/lib/mysql", берем левую часть
volumes=$(yq eval '.services[].volumes[]' docker-compose*.yaml 2>/dev/null | cut -d':' -f1 | grep '^\./' | sort -u)

if [ -z "$volumes" ]; then
    echo "Локальные volumes (начинающиеся с ./) не найдены."
    exit 0
fi

# 2. Создание базы проекта на HDD
mkdir -p "$TARGET_DIR"

# 3. Обработка каждого тома
for vol in $volumes; do
    # Очищаем путь от ./ (например, "./db_data" -> "db_data")
    vol_clean=$(echo "$vol" | sed 's|^\./||')
    src_path="$PWD/$vol_clean"
    dst_path="$TARGET_DIR/$vol_clean"

    echo "Обработка: $vol_clean"

    # Создаем папки
    mkdir -p "$src_path"
    mkdir -p "$dst_path"

    # Если в локальной папке на SSD есть данные, а на HDD пусто — переносим
    if [ "$(ls -A "$src_path")" ] && [ ! "$(ls -A "$dst_path")" ]; then
        echo "  [>] Перенос начальных данных на HDD..."
        rsync -a "$src_path/" "$dst_path/"
        rm -rf "${src_path:?}/*"
    fi

    # 4. Добавляем в /etc/fstab (если еще нет)
    # Используем Bind Mount с nofail и зависимостью от HDD
    if ! grep -q "$dst_path" /etc/fstab; then
        echo "  [+] Добавление в fstab..."
        echo "$dst_path $src_path none defaults,bind,nofail,x-systemd.requires=/mnt/hdd_data 0 0" >> /etc/fstab
    fi
done

# 5. Применяем изменения
systemctl daemon-reload
mount -a

echo "--- Готово! Все тома проекта привязаны к HDD ---"
findmnt -R "$PWD"
