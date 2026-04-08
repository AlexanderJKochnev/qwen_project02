#!/bin/bash
SOURCE_DIR="/mnt/hdd_data/@dumps"
SNAP_ROOT="/mnt/hdd_data/@snapshots"
EXT_DEST="/mnt/external_backup"
DATE=$(date +%Y%m%d_%H%M)
NEW_SNAP="$SNAP_ROOT/snap_$DATE"

echo "--- Создание снимка и отправка ---"

# 1. Создаем Read-Only снапшот
sudo btrfs subvolume snapshot -r "$SOURCE_DIR" "$NEW_SNAP"
sync

# 2. Ищем предыдущий снапшот для инcremental send
PREV_SNAP=$(ls -1d $SNAP_ROOT/snap_* | tail -2 | head -1)

if [ "$PREV_SNAP" != "$NEW_SNAP" ] && [ -n "$PREV_SNAP" ]; then
    echo "Отправка изменений между $(basename $PREV_SNAP) и $(basename $NEW_SNAP)..."
    sudo btrfs send -p "$PREV_SNAP" "$NEW_SNAP" | sudo btrfs receive "$EXT_DEST"
else
    echo "Первая отправка (полная)..."
    sudo btrfs send "$NEW_SNAP" | sudo btrfs receive "$EXT_DEST"
fi

# 3. Очистка старых снапшотов локально (оставляем последние 3)
ls -1d $SNAP_ROOT/snap_* | head -n -3 | xargs -r sudo btrfs subvolume delete

echo "Готово. Данные на внешнем диске: $EXT_DEST"
