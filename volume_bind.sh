#!/bin/bash

# --- НАСТРОЙКИ ---
HDD_BASE="/mnt/hdd_data/projects"
PROJECT_NAME=$(basename "$PWD")
TARGET_DIR="$HDD_BASE/$PROJECT_NAME"

if [ "$(id -u)" -ne 0 ]; then echo "Запустите от sudo"; exit 1; fi

# Установка зависимости, если её нет (обычно в Debian это python3-yaml)
if ! python3 -c "import yaml" &>/dev/null; then
    echo "Установка python3-yaml..."
    apt update && apt install -y python3-yaml
fi

echo "--- Анализ проекта через Python: $PROJECT_NAME ---"

# 1. Python-скрипт для извлечения ТОЛЬКО локальных томов (./)
# Он объединяет все найденные docker-compose*.yaml в один список уникальных путей
volumes=$(python3 -c "
import yaml, glob, os
vols = set()
for f in glob.glob('docker-compose*.yaml'):
    try:
        with open(f, 'r') as stream:
            data = yaml.safe_load(stream)
            if not data or 'services' not in data: continue
            for service in data['services'].values():
                v = service.get('volumes', [])
                if isinstance(v, list):
                    for entry in v:
                        # Берем левую часть до двоеточия и чистим кавычки
                        path = entry.split(':')[0].strip()
                        if path.startswith('./'):
                            vols.add(path)
    except Exception: pass
print('\n'.join(sorted(vols)))
")

if [ -z "$volumes" ]; then
    echo "Локальные тома (./) не найдены в секциях volumes."
    exit 0
fi

# 2. Интерактивная часть
echo "Найдены тома для привязки к HDD:"
echo "$volumes" | sed 's/^/  [ ] /'
echo "------------------------------------------"
read -p "Перенести данные и примонтировать к HDD? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Отмена."
    exit 0
fi

# 3. Очистка старых записей
echo "Очистка fstab от старых записей проекта..."
umount -l "$PWD"/* 2>/dev/null
sed -i "\|$PWD|d" /etc/fstab

# 4. Обработка
mkdir -p "$TARGET_DIR"

for vol in $volumes; do
    vol_clean=$(echo "$vol" | sed 's|^\./||')
    src_path="$PWD/$vol_clean"
    dst_path="$TARGET_DIR/$vol_clean"

    echo "Настройка: $vol_clean"
    mkdir -p "$src_path" "$dst_path"

    # Перенос данных, если на HDD пусто
    if [ "$(ls -A "$src_path" 2>/dev/null)" ] && [ ! "$(ls -A "$dst_path" 2>/dev/null)" ]; then
        echo "  [>] Перенос данных на HDD..."
        rsync -a "$src_path/" "$dst_path/"
        find "$src_path" -mindepth 1 -delete
    fi

    # Запись в fstab (Bind Mount)
    echo "$dst_path $src_path none defaults,bind,nofail,x-systemd.requires=/mnt/hdd_data 0 0" >> /etc/fstab
done

systemctl daemon-reload
mount -a

echo "--- ГОТОВО ---"
findmnt -R "$PWD"
