#!/bin/bash

HDD_BASE="/mnt/hdd_data/projects"
PROJECT_NAME=$(basename "$PWD")
TARGET_DIR="$HDD_BASE/$PROJECT_NAME"

if [ "$(id -u)" -ne 0 ]; then echo "Ошибка: запустите от sudo"; exit 1; fi

echo "--- Анализ проекта: $PROJECT_NAME ---"

# 1. Извлекаем тома через Python (теперь возвращаем кортеж путь:тип)
volumes=$(python3 -c "
import yaml, glob, os
vols = set()
for f in glob.glob('docker-compose*.yaml'):
    try:
        with open(f, 'r') as stream:
            data = yaml.safe_load(stream)
            if not data or 'services' not in data: continue
            for service in data.get('services', {}).values():
                v_list = service.get('volumes', [])
                if isinstance(v_list, list):
                    for entry in v_list:
                        if isinstance(entry, str) and entry.startswith('./'):
                            path = entry.split(':')[0]
                            # Проверяем, существует ли это уже как файл или папка
                            vols.add(path)
    except Exception: pass
print('\n'.join(sorted(vols)))
")

if [ -z "$volumes" ]; then
    echo "Локальные тома (./) не найдены."
    exit 0
fi

echo -e "\nНайдены тома для переноса:\n--------------------------"
echo "$volumes" | sed 's/^/  [ ] /'
echo -n "--------------------------\nДобавить в fstab? (y/n): "
read -r CONFIRM < /dev/tty

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "Отмена."; exit 0
fi

# 2. Очистка старых записей
sed -i "\|$TARGET_DIR|d" /etc/fstab

# 3. Обработка
mkdir -p "$TARGET_DIR"

for vol in $volumes; do
    vol_clean=$(echo "$vol" | sed 's|^\./||')
    src_path="$PWD/$vol_clean"
    dst_path="$TARGET_DIR/$vol_clean"

    echo "Настройка: $vol_clean"

    # ОПРЕДЕЛЯЕМ: ФАЙЛ ИЛИ ПАПКА
    if [ -f "$src_path" ]; then
        # Это файл
        mkdir -p "$(dirname "$dst_path")"
        touch "$dst_path"
        # Если файл на SSD не пуст, а на HDD пуст - копируем
        [ -s "$src_path" ] && [ ! -s "$dst_path" ] && cp "$src_path" "$dst_path"
    else
        # Это директория
        mkdir -p "$src_path" "$dst_path"
        if [ "$(ls -A "$src_path" 2>/dev/null)" ] && [ ! "$(ls -A "$dst_path" 2>/dev/null)" ]; then
            echo "  [>] Перенос данных..."
            rsync -a "$src_path/" "$dst_path/"
            find "$src_path" -mindepth 1 -delete
        fi
    fi

    # Добавляем в fstab
    echo "$dst_path $src_path none defaults,bind,nofail,x-systemd.requires=/mnt/hdd_data 0 0" >> /etc/fstab
done

systemctl daemon-reload
mount -a

echo -e "\n--- ГОТОВО. Проверка монтирования в текущей папке: ---"
findmnt -R "$PWD"
