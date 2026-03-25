##  проверка/подготовка дисков
1. sudo apt install nvme-cli smartmontools lshw pciutils hdparm fio
2. nvme list
   1. /dev/ng1n1  #  PHLF730100NN1P0GGN   INTEL SSDPE2KX010T7                      0x1          1.00  TB /   1.00  TB    512   B +  0 B   QDV10170
   2. /dev/ng0n1  #  P320PDBB250718003134 Patriot M.2 P320 256GB                   0x1        256.06  GB / 256.06  GB    512   B +  0 B   GT29c363
3. nvme id-ctrl /dev/ng1n1  # общая информация
4. nvme id-ns /dev/ng1n1  # информация о пространстве имен
5. nvme smart-log /dev/ng1n1  # smart
6. smartctl -a /dev/ng1n1  # smart ext
7. lspci -vvv -s $(lspci | grep "Non-Volatile memory controller" | head -1 | cut -d' ' -f1)  # скорость соедиения
8. watch -n 1 sudo nvme smart-log /dev/ng1n1

## форматирование диска и замена
1. # Показать все точки монтирования с информацией о файловой системе
   findmnt -D
   # Или более детальная информация
   df -hT
2. # Показать все диски и разделы
   lsblk
3. # Показать диски с моделью (чтобы убедиться, что мы работаем с правильным железом)
   lsblk -o NAME,SIZE,MODEL,MOUNTPOINT
4. # Узнать UUID дисков (очень пригодится для fstab)
   sudo blkid
5. # Узнать, где Docker хранит данные (data-root)
   docker info | grep "Docker Root Dir"  # Docker Root Dir: /var/lib/docker
6. # Посмотреть все volumes и их расположение на диске
   docker volume ls
   docker volume inspect $(docker volume ls -q) | grep -E "Name|Mountpoint"
7. # Посмотреть записи автоматического монтирования
   cat /etc/fstab
   # Посмотреть реально смонтированные (включая те, что не в fstab)
   mount
## STEP 2 ОЧИСТКА И РАЗМЕТКА
1. # Проверим, нет ли активных монтирований
   sudo umount /dev/nvme1n1* 2>/dev/null
   sudo dmsetup remove_all 2>/dev/null
2. # Очистим диск от существующих разделов и файловых систем
   sudo wipefs -a /dev/nvme1n1
3. # Создаем таблицу разделов GPT
   sudo parted /dev/nvme1n1 mklabel gpt

   # Создаем один раздел на весь диск
   sudo parted /dev/nvme1n1 mkpart primary 0% 100%
4. # Посмотрим новый раздел
   lsblk /dev/nvme1n1

   # Должны увидеть примерно такое:
   # NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT
   # nvme1n1     259:0    0 931.5G  0 disk 
   # └─nvme1n1p1 259:1    0 931.5G  0 part

## STEP.3. форматирование
1. # Устанавливаем пакет btrfs-progs
   sudo apt update
   sudo apt install -y btrfs-progs
2. # Должна показаться версия
   mkfs.btrfs --version
3. # Используем флаг -f для принудительной перезаписи
   sudo mkfs.btrfs -f /dev/nvme1n1p1
4. # Создаем временную точку монтирования (если еще не создана)
   sudo mkdir -p /mnt/new_disk_temp
5. # Монтируем с опцией noatime
   sudo mount -o noatime /dev/nvme1n1p1 /mnt/new_disk_temp
6. # Создаем структуру директорий
   sudo mkdir -p /mnt/new_disk_temp/{log,volumes,projects}
   sudo mkdir -p /mnt/new_disk_temp/projects/wine/{nginx,mongodb_data,pg_data,pg_dump,preact_front,templates,upload_volume,migration_volume}
   sudo mkdir -p /mnt/new_disk_temp/projects/wine/nginx/{conf.d,static}
   sudo mkdir -p /mnt/new_disk_temp/projects/wine/preact_front/{public,src}
   sudo mkdir -p /mnt/new_disk_temp/projects/{ollama,netdata,kanboard,test}
7. # Устанавливаем NOCOW для директорий с базами данных
   sudo chattr +C /mnt/new_disk_temp/projects/wine/pg_data
   sudo chattr +C /mnt/new_disk_temp/projects/wine/pg_dump
   sudo chattr +C /mnt/new_disk_temp/projects/wine/mongodb_data
   sudo chattr +C /mnt/new_disk_temp/volumes
   sudo chattr +C /mnt/new_disk_temp/log
   sudo chattr +C /mnt/new_disk_temp/projects/test
8. # Проверяем атрибуты
   lsattr /mnt/new_disk_temp/projects/wine/
   lsattr /mnt/new_disk_temp/volumes
   lsattr /mnt/new_disk_temp/log
## STEP.4. перенос данных 
9. # Сохраним список всех bind mounts из fstab для истории
   cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d)
10. # Покажем текущие монтирования старого диска
   echo "=== Текущие монтирования старого диска ==="
   mount | grep /dev/sda
11. # Переносим основную точку монтирования (содержимое /mnt/hdd_data)
   sudo rsync -avxHAX --progress /mnt/hdd_data/ /mnt/new_disk_temp/
12. # Проверим размеры
   echo "Старый диск:"
   df -h /mnt/hdd_data
   echo "Новый диск:"
   df -h /mnt/new_disk_temp
13. # Выборочно проверим несколько важных директорий
   ls -la /mnt/new_disk_temp/projects/wine/pg_data/
   ls -la /mnt/new_disk_temp/volumes/
   ls -la /mnt/new_disk_temp/log/
14. # Сравним права нескольких ключевых файлов/директорий
   echo "=== Права на старом диске ==="
   stat /mnt/hdd_data/volumes
   stat /mnt/hdd_data/log

   echo "=== Права на новом диске ==="
   stat /mnt/new_disk_temp/volumes
   stat /mnt/new_disk_temp/log

## STEP.5. STOP SERVICES
1. # Останавливаем Docker (он основной потребитель)
   sudo systemctl stop docker
   sudo systemctl stop docker.socket
2. # Проверяем, что Docker остановлен
   sudo systemctl status docker --no-pager
3. # Останавливаем системный журнал (он пишет в /var/log на старом диске)
   sudo systemctl stop rsyslog
   sudo systemctl stop systemd-journald
4. # Останавливаем возможные сервисы баз данных (если они запущены не в Docker)
   sudo systemctl stop postgresql mongodb 2>/dev/null
5. # Останавливаем nginx если он запущен на хосте (не в Docker)
   sudo systemctl stop nginx 2>/dev/null
6. # Проверяем открытые файлы на старом диске
   sudo lsof | grep /mnt/hdd_data
7. # Если есть процессы, использующие диск, их нужно остановить
8. # Например: sudo systemctl stop <имя_сервиса>
9. # Создаем резервную копию fstab
   sudo cp /etc/fstab /etc/fstab.backup.before_swap
10. # Показываем текущие записи, связанные со старым диском
   echo "=== Текущие записи в fstab ==="
   grep -n "/mnt/hdd_data" /etc/fstab

## STEP.6. SWAP
1. # Сначала размонтируем все bind mounts (обратный порядок)
   sudo umount /var/lib/docker/volumes
   sudo umount /home/alex/dockers/wine/upload_volume
   sudo umount /home/alex/dockers/wine/templates
   sudo umount /home/alex/dockers/wine/preact_front/src
   sudo umount /home/alex/dockers/wine/preact_front/public
   sudo umount /home/alex/dockers/wine/preact_front/package.json
   sudo umount /home/alex/dockers/wine/pg_dump
   sudo umount /home/alex/dockers/wine/pg_data
   sudo umount /home/alex/dockers/wine/nginx/static
   sudo umount /home/alex/dockers/wine/nginx/conf.d
   sudo umount /home/alex/dockers/wine/mongodb_data
   sudo umount /home/alex/dockers/wine/migration_volume
   sudo umount /var/log
2. # Проверим процессы, использующие /var/log
   sudo lsof | grep /var/log
3. # Также проверим монтирования внутри /var/log
   mount | grep /var/log
4. # Останавливаем fail2ban
   sudo systemctl stop fail2ban
5. # Останавливаем proftpd
   sudo systemctl stop proftpd
6. # Проверяем, что они остановлены
   sudo systemctl status fail2ban --no-pager
   sudo systemctl status proftpd --no-pager
7. # Сначала проверяем, не появились ли новые процессы
   sudo lsof | grep /var/log
8. # Если ничего нет, размонтируем
   sudo umount /var/log
9. # Проверяем результат
   mount | grep /var/log

10. # Проверим, что никто не использует
   sudo lsof | grep /mnt/hdd_data
11. # Размонтируем основной диск
   sudo umount /mnt/hdd_data
12. # Проверим результат
   lsblk /dev/sda
   mount | grep /dev/sda

## STEP.6.2. монтируем новый диск
1. # Получаем UUID нового диска
   sudo blkid /dev/nvme1n1p1
2. # Создаем резервную копию текущего fstab
   sudo cp /etc/fstab /etc/fstab.backup.$(date +%Y%m%d_%H%M%S)
3. # Редактируем fstab
   sudo nano /etc/fstab
4. # Заменить строку 20 строкой
   UUID=новый_uuid /mnt/hdd_data btrfs defaults,noatime 0 2
5. # Перезагружаем systemd
   sudo systemctl daemon-reload
6. # Монтируем все согласно новому fstab
   sudo mount -a
7. # Проверяем результат
   df -h /mnt/hdd_data
   lsblk /dev/nvme1n1
   mount | grep nvme1n1
8. # Проверяем ключевые точки
   df -h /var/lib/docker/volumes
   df -h /home/alex/dockers/wine/pg_data
   df -h /var/log

## STEP.7. запуск сервисов
1. # Запускаем Docker
   sudo systemctl start docker
2. # Проверяем статус
   sudo systemctl status docker --no-pager
3. # Проверяем, что Docker видит свои volumes
   docker volume ls
4. # Запускаем fail2ban и proftpd
   sudo systemctl start fail2ban
   sudo systemctl start proftpd
5. # Проверяем их статус
   sudo systemctl status fail2ban --no-pager
   sudo systemctl status proftpd --no-pager
6. # Создадим тестовую запись в логах
   logger "Test log entry after disk replacement"
7. # Проверим, что появилась запись
   tail -n 5 /var/log/syslog 2>/dev/null || tail -n 5 /var/log/messages 2>/dev/null

## STEP.8. Восстановление баз данных
1. # Проверим права на директорию PostgreSQL
   ls -la /home/alex/dockers/wine/pg_data/
2. # Если PostgreSQL запускается в Docker, запустите контейнер
   cd /home/alex/dockers/wine  # или где у вас docker-compose.yml
   docker-compose up -d postgres  # или имя вашего сервиса
3. # Проверим логи PostgreSQL
   docker logs <имя_контейнера_postgres> --tail 50
4. # Запускаем MongoDB контейнер
   docker-compose up -d mongodb  # или имя вашего сервиса
5. # Проверяем логи
   docker logs <имя_контейнера_mongodb> --tail 50
6. # Проверяем использование диска
   df -h
7. # Проверяем, что все сервисы работают
   systemctl status docker fail2ban proftpd --no-pager
8. # Проверяем, что новые данные пишутся на новый диск
9. # Создадим тестовый файл в volumes
   touch /var/lib/docker/volumes/test_file
   ls -la /var/lib/docker/volumes/

## STEP.9. очистка
1. # Размонтируем временную точку
   sudo umount /mnt/new_disk_temp
   sudo rmdir /mnt/new_disk_temp
2. # Удаляем временную копию логов (если создавали)
   sudo rm -rf /var/log.tmp 2>/dev/null
3. # Проверим, что старый диск не используется
   lsblk /dev/sda
4. # Можно затереть служебные метки (чтобы случайно не примонтировать)
   sudo wipefs -a /dev/sda

## STEP.10. НАСТРОЙКА SNAPSHOTS
1. # Создадим скрипт для снапшотов
   sudo mkdir -p /usr/local/bin
   sudo nano /usr/local/bin/make_snapshot.sh
#!/bin/bash
SNAPSHOT_DIR="/mnt/hdd_data/.snapshots"
DATE=$(date +%Y%m%d_%H%M%S)

# Создаем директорию для снапшотов если нет
mkdir -p $SNAPSHOT_DIR

# Создаем снапшот
btrfs subvolume snapshot -r /mnt/hdd_data $SNAPSHOT_DIR/snap_$DATE

# Удаляем снапшоты старше 7 дней
find $SNAPSHOT_DIR -name "snap_*" -type d -mtime +7 -exec btrfs subvolume delete {} \;

2. sudo crontab -e
   # Добавить строку для снапшота каждые 15 минут:
   */15 * * * * /usr/local/bin/make_snapshot.sh
3. проверка сколько мета занимают снапшоты
   sudo btrfs filesystem du -s /mnt/hdd_data/.snapshots/* | sort -h
## useful tips
# 1. Общее использование диска
sudo btrfs filesystem usage /mnt/hdd_data

# 2. Использование по подтомам (включая снапшоты)
sudo btrfs subvolume list /mnt/hdd_data

# 3. Детальная информация о каждом снапшоте
for snap in /mnt/hdd_data/.snapshots/*; do
    echo "=== $snap ==="
    sudo btrfs filesystem du -s "$snap"
done

# 4. Разница между снапшотами
sudo btrfs send --no-data -p /mnt/hdd_data/.snapshots/snap_old /mnt/hdd_data/.snapshots/snap_new | wc -c
# Покажет размер изменений в байтах