#!/bin/bash
# Настройки
HDD_DEV="/dev/sda"             # ПРОВЕРЬТЕ ПРАВИЛЬНОСТЬ ЧЕРЕЗ lsblk!
MOUNT_POINT="/mnt/hdd_data"
DOCKER_LIB="/var/lib/docker"
LOG_DIR="/var/log"

# Проверка на root
if [[ $EUID -ne 0 ]]; then
   echo "Запустите скрипт от имени root (sudo)"
   exit 1
fi

echo "!!! ВНИМАНИЕ: Диск $HDD_DEV будет отформатирован. Все данные будут удалены !!!"
read -p "Вы уверены? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# 1. Остановка сервисов (обязательно перед манипуляциями с логами)
systemctl stop docker docker.socket containerd 2>/dev/null
systemctl stop rsyslog 2>/dev/null

# 2. Подготовка диска (Размонтирование, форматирование, монтирование)
umount $HDD_DEV 2>/dev/null
echo "Форматирование $HDD_DEV в ext4..."
mkfs.ext4 -F $HDD_DEV

mkdir -p $MOUNT_POINT
mount $HDD_DEV $MOUNT_POINT

# 3. Настройка автомонтрирования через fstab
UUID=$(blkid -s UUID -o value $HDD_DEV)
sed -i "\|$MOUNT_POINT|d" /etc/fstab # Чистим старые записи для этого пути
echo "UUID=$UUID $MOUNT_POINT ext4 defaults 0 2" >> /etc/fstab

# 4. Функция переноса и создания ссылок
move_and_link() {
    local src=$1
    local dst=$2
    mkdir -p "$dst"
    
    if [ -d "$src" ] && [ ! -L "$src" ]; then
        echo "Перенос данных из $src на HDD..."
        rsync -a "$src/" "$dst/"
        rm -rf "$src"
    fi
    
    # Если папки нет (новый docker), просто создаем ссылку
    [ ! -e "$src" ] && ln -s "$dst" "$src"
    echo "Ссылка создана: $src -> $dst"
}

# 5. Выполнение линковки
# Только вольюмы на HDD, образы/контейнеры остаются на SSD (/var/lib/docker/overlay2)
move_and_link "$DOCKER_LIB/volumes" "$MOUNT_POINT/docker_volumes"
# Системные логи
move_and_link "$LOG_DIR" "$MOUNT_POINT/system_logs"
# Папка для бэкапов
move_and_link "/opt/backups" "$MOUNT_POINT/backups"

# 6. Возвращаем права (для логов важно)
chown root:syslog "$MOUNT_POINT/system_logs" 2>/dev/null
chmod 755 "$MOUNT_POINT/system_logs"

# 7. Запуск сервисов
systemctl start rsyslog 2>/dev/null
systemctl start docker 2>/dev/null

echo "Готово! HDD подготовлен, ссылки созданы."
lsblk $HDD_DEV
