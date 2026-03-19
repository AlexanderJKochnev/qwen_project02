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

## STEP.6.