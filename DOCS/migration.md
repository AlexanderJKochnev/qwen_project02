# DOCS/migration.md
##  переезд docker  c fat на btrfs
0. зачищаем хвосты
    sudo systemctl stop docker.socket docker
    sudo umount -l /var/lib/docker/volumes
    sudo umount -l /var/lib/docker
    mount | grep docker 
    Удаляем только внутренности папки docker на NVMe
    sudo rm -rf /mnt/hdd_data/docker/*
    sudo nano /etc/docker/daemon.json
{
  "storage-driver": "btrfs",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "100m",
    "max-file": "3"
  },
  "runtimes": {
    "nvidia": {
      "args": [],
      "path": "nvidia-container-runtime"
    }
  }
}
    sudo mount --bind /mnt/hdd_data/docker /var/lib/docker
    sudo systemctl start docker
    docker info | grep "Storage Driver"

1. docker pull
2. docker run --rm ghcr.io/alexanderjkochnev/nginx1.28.1:stable-alpine id nginx  # проверка прав
3. docker run --rm -v certs_data:/data alpine ls -la /data/live/abc8888.ru/
4. ls -la ${PWD}/.htpasswd
5. docker exec nginx_gateway ls -la /etc/nginx/.htpasswd
6. docker-compose up -d --force-recreate

### восстановление данных из snapshot
1. sudo systemctl stop docker.socket docker
2. sudo umount -l /var/lib/docker/volumes 
3. sudo umount -l /var/lib/docker
4. sudo ls -la /mnt/hdd_data/snapshot_clean_before_btrfs_driver/volumes
5. sudo du -sh /mnt/hdd_data/.snapshots/snap_20260402_180001/volumes  #  размер данных в snapshot
6. sudo systemctl stop docker.socket docker 
7. sudo umount -l /var/lib/docker/volumes 
8. sudo rm -rf /mnt/hdd_data/volumes/*
мгновенное восстановление:
9. sudo cp -a --reflink=always /mnt/hdd_data/.snapshots/snap_20260402_180001/volumes/. /mnt/hdd_data/volumes/
монтируем обратно
10. sudo mount --bind /mnt/hdd_data/docker /var/lib/docker
11. очистить если там что-то есть (акурfтно с volumes)
12. sudo systemctl start docker

### создание subvolume
1. sudo btrfs subvolume create ./docker_subvolume
2. sudo mv /mnt/hdd_data/volumes /mnt/hdd_data/volumes_bak
3. sudo btrfs subvolume create /mnt/hdd_data/volumes  # создание субтома
4. sudo cp -a --reflink=always /mnt/hdd_data/volumes_bak/. /mnt/hdd_data/volumes/  # перенос диретории в субтом
5. sudo cp -p /mnt/hdd_data/volumes_bak/metadata.db /mnt/hdd_data/volumes/
6. ls -la /mnt/hdd_data/volumes
7. sudo mv /mnt/hdd_data/docker /mnt/hdd_data/docker_old
8. sudo btrfs subvolume create /mnt/hdd_data/docker
# Останавливаем Docker (на всякий случай еще раз)
sudo systemctl stop docker.socket docker

# Размонтируем всё, что связано с Docker, принудительно
sudo umount -l /var/lib/docker/volumes 2>/dev/null
sudo umount -l /var/lib/docker 2>/dev/null

blkid /dev/nvme1n1p1   UUID="42ca1166-9334-4fc4-8405-c89ebcd3030f"
sudo mount -t btrfs -o subvol=docker /dev/nvme1n1p1 /var/lib/docker
# Сначала создадим точку внутри, так как диск теперь чистый
sudo mkdir -p /var/lib/docker/volumes
sudo mount -t btrfs -o subvol=volumes /dev/nvme1n1p1 /var/lib/docker/volumes
UUID=42ca1166-9334-4fc4-8405-c89ebcd3030f /var/lib/docker         btrfs  subvol=docker,defaults,noatime  0  2
UUID=42ca1166-9334-4fc4-8405-c89ebcd3030f /var/lib/docker/volumes btrfs  subvol=volumes,defaults,noatime 0  2
 # проверка
sudo systemctl daemon-reload
sudo mount -a
sudo systemctl start docker
docker info | grep "Storage Driver"

# получение UID пользователя в контейнере
docker exec -it kanboard id nginx
uid=100(nginx) gid=101(nginx) groups=101(nginx),82(www-data),101(nginx)
в docker compose в секцию сервиса добавить 
    user: "100:101"

ls -ld /home/alex/dockers/test/pg_data /home/alex/dockers/test/mongodb_data
drwxr-xr-x  3 999 root 4096 Apr  2 16:16 /home/alex/dockers/test/mongodb_data
drwx------ 19  70 root 4096 Apr  2 16:42 /home/alex/dockers/test/pg_data
alex@debby13:/mnt/hdd_data$ ls -ld /home/alex/dockers/test/pg_data /home/alex/dockers/test/mongodb_data
drwxr-xr-x  3 999 root 4096 Apr  2 16:16 /home/alex/dockers/test/mongodb_data
drwx------ 19  70 root 4096 Apr  2 16:42 /home/alex/dockers/test/pg_data

docker run --rm ghcr.io/alexanderjkochnev/postgres:17-alpine id postgres
uid=70(postgres) gid=70(postgres) groups=70(postgres),70(postgres)

docker run --rm ghcr.io/alexanderjkochnev/mongo:4.4.20 id mongodb 2>/dev/null || docker run --rm ghcr.io/alexanderjkochnev/mongo:4.4.20 id root
uid=999(mongodb) gid=999(mongodb) groups=999(mongodb)

## ПЕРЕНОС С exfat на btrfs COURSE OF ACTIONS
1. где сейчас данные volumes (см docker compose)
2. Содержимое fstab: cat /etc/fstab | grep btrfs
3. Текущее состояние монтирования:
   1. mount | grep btrfs 
   2. df -h /var/lib/docker   # если docker на btrfs
4. Путь к данным ClickHouse на хосте: 
5. ОБЩИЙ ШАБЛОН КОМАНД:
# 1. Остановка контейнера
docker-compose stop clickhouse

# 2. Создание временной директории для бэкапа
sudo mkdir -p /mnt/hdd_data/tmp_clickhouse_migration

# 3. Копирование существующих данных во временное место (с сохранением атрибутов)
sudo cp -a --reflink=always /mnt/hdd_data/volumes/clickhouse/ch_data/* /mnt/hdd_data/tmp_clickhouse_migration/
# Сравнение для того что бы проверить полноту и корректность копирования
du -sh /mnt/hdd_data/volumes/clickhouse/ch_data/
du -sh /mnt/hdd_data/tmp_clickhouse_migration/
ls -la /mnt/hdd_data/volumes/clickhouse/ch_data/
ls -la /mnt/hdd_data/tmp_clickhouse_migration/

# 4. Удаление старой директории (после проверки копирования!)
sudo rm -rf /mnt/hdd_data/volumes/clickhouse/ch_data

# 5. Создание subvolume на btrfs
    # Создаем subvolume в том же месте
sudo btrfs subvolume create /mnt/hdd_data/volumes/clickhouse/ch_data

    # Проверяем создание
sudo btrfs subvolume list /mnt/hdd_data | grep clickhouse

## проверка что объект является subvolume
    sudo btrfs subvolume show /mnt/hdd_data/volumes/clickhouse/ch_data

# 6. Монтирование subvolume в старую директорию (ОБЯЗАТЕЛЬНО!) 
sudo mount -t btrfs -o subvol=volumes/clickhouse/ch_data /dev/nvme1n1p1 /mnt/hdd_data/volumes/clickhouse/ch_data

# 7. Копирование данных из временной папки в subvolume (с reflink!)
sudo cp -a --reflink=always /mnt/hdd_data/tmp_clickhouse_migration/* /mnt/hdd_data/volumes/clickhouse/ch_data/

# 8. Проверка и исправление прав (UID=101 для ClickHouse) НЕ ДЕЛАТЬ - НЕ МЕШАТЬ DOCKER
    # ClickHouse внутри контейнера работает от UID 101:GID 101 
sudo chown -R 101:101 /mnt/hdd_data/volumes/clickhouse/ch_data

    # Проверяем права (НЕТ СМЫСЛА
ls -la /mnt/hdd_data/volumes/clickhouse/ch_data

# 9. Добавление в fstab для автоматического монтирования
sudo nano /etc/fstab
UUID=42ca1166-9334-4fc4-8405-c89ebcd3030f /mnt/hdd_data/volumes/clickhouse/ch_data btrfs subvol=volumes/clickhouse/ch_data,defaults,noatime 0 0

# 9.1. Применение изменений
# Применяем изменения из fstab
sudo systemctl daemon-reload
sudo mount -a

# Проверяем, что subvolume примонтирован правильно
mount | grep "clickhouse/ch_data"

# 10. Запуск контейнера
docker-compose up -d

# 11. Если всё работает, удалите временную папку
sudo rm -rf /mnt/hdd_data/tmp_clickhouse_migration