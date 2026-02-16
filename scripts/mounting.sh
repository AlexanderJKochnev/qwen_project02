#!/bin/bash

# --- НАСТРОЙКИ ---
HDD_DEV="/dev/sda"        # Целевой диск
MOUNT_POINT="/mnt/hdd_data"
LOG_DIR="/var/log"
DOCKER_VOLUMES="/var/lib/docker/volumes"

# Проверка прав root
if [[ $EUID -ne 0 ]]; then echo "Ошибка: Запустите от sudo"; exit 1; fi

echo "--- Начинаю замену/настройку диска $HDD_DEV ---"

# 1. Установка необходимых утилит
apt update && apt install -y e2fsprogs rsync 2>/dev/null

# 2. Остановка зависимых сервисов
systemctl stop docker 2>/dev/null
systemctl stop proftpd 2>/dev/null

# 3. Полная очистка fstab от старых записей этого диска и его bind-монтирований
sed -i "\|$MOUNT_POINT|d" /etc/fstab
sed -i "\|/var/log|d" /etc/fstab
sed -i "\|/var/lib/docker/volumes|d" /etc/fstab

# 4. Форматирование в ext4
umount -l $HDD_DEV 2>/dev/null
echo "Форматирование $HDD_DEV..."
mkfs.ext4 -F $HDD_DEV || { echo "Ошибка форматирования!"; exit 1; }

# 5. Монтирование и получение нового UUID
mkdir -p $MOUNT_POINT
UUID=$(blkid -s UUID -o value $HDD_DEV)
mount -U $UUID $MOUNT_POINT || { echo "Ошибка монтирования!"; exit 1; }

# 6. Подготовка структуры папок на самом HDD
mkdir -p "$MOUNT_POINT/log"
mkdir -p "$MOUNT_POINT/volumes"
chown root:adm "$MOUNT_POINT/log"
chmod 755 "$MOUNT_POINT/log"

# 7. Запись в /etc/fstab (Используем Bind Mount для стабильности)
echo "UUID=$UUID $MOUNT_POINT ext4 defaults,nofail,x-systemd.device-timeout=10s 0 2" >> /etc/fstab
echo "$MOUNT_POINT/log /var/log none defaults,bind,nofail,x-systemd.requires=$MOUNT_POINT 0 0" >> /etc/fstab
echo "$MOUNT_POINT/volumes /var/lib/docker/volumes none defaults,bind,nofail,x-systemd.requires=$MOUNT_POINT 0 0" >> /etc/fstab

# 8. Финальная проверка и применение
systemctl daemon-reload
mount -a

# 9. Запуск сервисов
systemctl start docker 2>/dev/null
systemctl start proftpd 2>/dev/null

echo "--- ГОТОВО ---"
echo "Диск $HDD_DEV настроен. UUID: $UUID"
findmnt /var/log
