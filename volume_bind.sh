#!/bin/bash

# --- НАСТРОЙКИ ---
HDD_BASE="/mnt/hdd_data/projects"
PROJECT_NAME=$(basename "$PWD")
TARGET_DIR="$HDD_BASE/$PROJECT_NAME"

if [ "$(id -u)" -ne 0 ]; then echo "Ошибка: запустите от sudo"; exit 1; fi

echo "--- Анализ проекта: $PROJECT_NAME ---"

# 1. Исправленный Python-блок (извлекает ТОЛЬКО левую часть до двоеточия)
volumes=$(python3 -c "
import yaml, glob
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
                            # Отсекаем правую часть и лишние пробелы
                            path = entry.split(':')[0].strip()
                            vols.add(path)
    except Exception: pass
print('\n'.join(sorted(vols)))
")

if [ -z "$volumes" ]; then
    echo "Локальные тома (./) в секциях volumes: не найдены."
    exit 0
fi

# 2. ИНТЕРАКТИВНЫЙ БЛОК
echo ""
echo "Найдены следующие тома для привязки к HDD:"
echo "------------------------------------------"
echo "$volumes" | sed 's/^/  [ ] /'
echo "------------------------------------------"

# Читаем ответ именно из терминала (/dev/tty), чтобы не проскакивало
echo -n "Добавить эти тома в fstab и перенести данные на HDD? (y/n): "
read -r CONFIRM < /dev/tty

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "Операция отменена. Никаких изменений не внесено."
    exit 0
fi

# 3. ОЧИСТКА (удаляем старые записи этого проекта из fstab)
echo "Очистка fstab от старых записей проекта $PROJECT_NAME..."
# Размонтируем текущие папки, если они были примонтированы
for vol in $volumes; do
    vol_clean=$(echo "$vol" | sed 's|^\./||')
    umount -l "$PWD/$vol_clean" 2>/dev/null
done
sed -i "\|$TARGET_DIR|d" /etc/fstab

# 4. ОБРАБОТКА И ЗАПИСЬ
mkdir -p "$TARGET_DIR"

for vol in $volumes; do
    vol_clean=$(echo "$vol" | sed 's|^\./||')
    src_path="$PWD/$vol_clean"
    dst_path="$TARGET_DIR/$vol_clean"

    echo "Настройка: $vol_clean"
    mkdir -p "$src_path" "$dst_path"

    # Перенос данных, если на SSD есть, а на HDD пусто
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

echo ""
echo "--- ГОТОВО ---"
findmnt -R "$PWD"
