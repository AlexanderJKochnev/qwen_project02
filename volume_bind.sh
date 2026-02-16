#!/bin/bash

# --- НАСТРОЙКИ ---
HDD_BASE="/mnt/hdd_data/projects"
PROJECT_NAME=$(basename "$PWD")
TARGET_DIR="$HDD_BASE/$PROJECT_NAME"

if [ "$(id -u)" -ne 0 ]; then echo "Запустите от sudo"; exit 1; fi

echo "--- Настройка проекта: $PROJECT_NAME ---"

# 1. Извлекаем пути томов прямо из файлов (ищем строки с ./ и :)
# Убираем лишние пробелы, тире, кавычки и всё после двоеточия
volumes=$(grep -h "\./" docker-compose*.yaml | sed -e 's/^[[:space:]]*- //' -e 's/["'\'']//g' | cut -d':' -f1 | sort -u)

if [ -z "$volumes" ]; then
    echo "Ошибка: Локальные тома не найдены в docker-compose файлах."
    exit 1
fi

# 2. Подготовка базы на HDD
mkdir -p "$TARGET_DIR"

# 3. Обработка каждого тома
for vol in $volumes; do
    # Убираем ./ (например, ./pg_data -> pg_data)
    vol_clean=$(echo "$vol" | sed 's|^\./||')
    src_path="$PWD/$vol_clean"
    dst_path="$TARGET_DIR/$vol_clean"

    echo "Настройка: $vol_clean"

    # Создаем папки
    mkdir -p "$src_path"
    mkdir -p "$dst_path"

    # Перенос данных на HDD, если на SSD они есть, а на HDD пусто
    if [ -d "$src_path" ] && [ "$(ls -A "$src_path" 2>/dev/null)" ] && [ ! "$(ls -A "$dst_path" 2>/dev/null)" ]; then
        echo "  [>] Перенос данных на HDD..."
        rsync -a "$src_path/" "$dst_path/"
        # Очищаем папку на SSD, чтобы она стала пустой точкой монтирования
        find "$src_path" -mindepth 1 -delete
    fi

    # 4. Добавляем в /etc/fstab (Bind Mount)
    if ! grep -q "$dst_path $src_path" /etc/fstab; then
        echo "  [+] Добавление в fstab..."
        echo "$dst_path $src_path none defaults,bind,nofail,x-systemd.requires=/mnt/hdd_data 0 0" >> /etc/fstab
    fi
done

# 5. Применяем изменения
systemctl daemon-reload
mount -a

echo "--- Готово! Проверка монтирования ---"
findmnt -R "$PWD"
