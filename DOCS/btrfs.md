## BTRFS QUICK MANUAL
## план
1. хранение:
   1. базы данных и другие named_volumes размещаем  в /mnt/hdd_data/@named_volumes/директория (No-CoW)
   2. бэкап /mnt/hdd_data/@dumps  (CoW)
   3. snapshots of backup /mnt/hdd_data/@snapshots  (CoW)
   4. внешний диск /dev/sda


### создание subvolume (собака просто что бы отличать subvolume от directory)
sudo btrfs subvolume create /mnt/hdd_data/@named_volumes

## проверка что объект является subvolume
    chdd_data/@named_volumes

## установка No-Cow на subvolume / directory - все НОВЫЕ  файлы и папки созданне в ней после этого будут No-Cow
sudo chattr +C /mnt/hdd_data/@named_volumes

# Проверить, что атрибут установлен (должна быть буква 'C' в выводе)
lsattr -d /mnt/hdd_data/@named_volumes

# ОЧИСТКА
1. ### поиск хвостов:
    sudo btrfs subvolume list /mnt/hdd_data
2. ### удаление строки аналогичные этой - хвосты от жизнедеятльености docker (смело удаляем)
    ID 2008 gen 46466 top level 1183 path docker/btrfs/subvolumes/pmmnebs83r7s5tsvwbl67zfbj
    скрипт usr/local/bin/del_garb.sh  !внимательно
    sudo btrfs subvolume delete <path без slash впереди>
3. ### балансировка
4. sudo btrfs balance start -dusage=1 /mnt/hdd_data

# БЭКАП
1. ### Подготовка внешнего диска (/dev/sda):
# Форматируем в Btrfs
sudo mkfs.btrfs -L "BACKUP_DRIVE" /dev/sda
# Создаем точку монтирования и монтируем
sudo mkdir -p /mnt/external_backup
sudo mount /dev/sda /mnt/external_backup
# прописываем в /etc/fstab
# Внешний диск для бэкапов
UUID="bd49248e-a092-46b9-8107-d2e3fcd474ae" /mnt/external_backup btrfs defaults,noatime,compress=zstd,nofail 0 2
sudo blkid /dev/sda
## проверка что объект является subvolume
    sudo btrfs subvolume show /mnt/external_backup
2. ### Настройка субтомов (сжатие):
# Включаем сжатие на папку с дампами
sudo chattr -C /mnt/hdd_data/@dumps  # Убеждаемся, что CoW ВКЛЮЧЕН
sudo btrfs property set /mnt/hdd_data/@dumps compression zstd

3. ### Скрипт создания дампов и ротации: scripts/dump_rotation/db_dump.sh
   usr/local/bin/db_dump.sh
4. ### Скрипт Снапшотов и отправки на внешний диск: scripts/dump_rotation/db-sync.sh
   /usr/local/bin/db-sync.sh
5. ### делаем их исполяемыми 
   sudo chmod +x /usr/local/bin/db-dump.sh /usr/local/bin/db-sync.sh
6. ### Автоматизация (Cron)
   sudo crontab -e
# Каждые 4 часа — делаем дампы всех БД (PG, Mongo, ClickHouse)
0 */4 * * * /usr/local/bin/db-dump.sh >> /var/log/db-backup.log 2>&1

# Раз в сутки (в 03:00) — делаем снапшот и отправляем на внешний диск
0 3 * * * /usr/local/bin/db-sync.sh >> /var/log/db-sync.log 2>&1

7. ### ротация логов
sudo nano /etc/logrotate.d/db-backups
/var/log/db-backup.log
/var/log/db-sync.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}