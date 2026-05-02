#!/bin/bash

# Пути
NOCOW_DIR="/mnt/hdd_data/@named_volumes/backup_tmp"
COW_DIR="/mnt/hdd_data/@dumps"
# seaweed делает инкрементальный backup поэтому немного другая логика
SEAWEED_BACKUP_DIR="/mnt/hdd_data/@named_volumes/seaweed_base"

# Создаем No-CoW зону, если нет (атрибут +C)
mkdir -p "$NOCOW_DIR" "$SEAWEED_BACKUP_DIR"
chattr +C "$NOCOW_DIR" "$SEAWEED_BACKUP_DIR" 2>/dev/null

echo "--- Начинаю создание дампов (No-CoW -> CoW) ---"

# 1. POSTGRES
echo "Dumping Postgres..."
docker exec -t prod-wine_host-1 pg_dumpall -c -U wine | gzip -n > "$NOCOW_DIR/pg.sql.gz"

# 2. MONGODB
echo "Dumping Mongo..."
docker exec prod-mongo-1 mongodump --username=admin --password=admin --authenticationDatabase=admin --archive --gzip > "$NOCOW_DIR/mg.archive.gz"

# 3. CLICKHOUSE
echo "Dumping ClickHouse..."
CH_SRC="/mnt/hdd_data/@named_volumes/clickhouse/ch_data/backups/my_dump"
rm -rf "$CH_SRC"
docker exec -u clickhouse clickhouse_search clickhouse-client --query="BACKUP DATABASE default TO File('my_dump')"
tar -cznf "$NOCOW_DIR/ch.tar.gz" -C "$CH_SRC" .
rm -rf "$CH_SRC"

# 4. SEAWEEDFS - бэкап ВСЕХ томов простым перебором (1-200)
echo "Backing up all SeaweedFS volumes incrementally..."
for VOL_ID in {1..200}; do
    docker exec seaweedfs_volume weed backup \
        -master=seaweedfs_master:9333 \
        -dir="$SEAWEED_BACKUP_DIR" \
        -volumeId=$VOL_ID 2>/dev/null
    # 2>/dev/null подавляет ошибки для несуществующих томов
done

# 3. Сохраняем статус кластера (для восстановления)
docker exec seaweedfs_master curl \
       -sS http://seaweedfs_master:9333/dir/status > "$SEAWEED_BACKUP_DIR/seaweed_status.json"

# --- СИНХРОНИЗАЦИЯ В CoW ЗОНУ ---
# rsync обновит файлы в @dumps только если они реально изменились.
# Флаг -c (checksum) заставит rsync сравнивать содержимое, а не дату/размер.
# Флаг --inplace важен для Btrfs CoW зоны.
echo "Синхронизация изменений..."
rsync -rc --inplace "$NOCOW_DIR/" "$COW_DIR/"
rsync -rc --inplace "$SEAWEED_BACKUP_DIR/" "$COW_DIR/"

rm -rf "$NOCOW_TMP"/*

echo "Готово. Актуальные дампы лежат в $COW_DIR"
