#!/bin/sh

# запускать в debian
# перемонтирует /var/lib/docker/image/  и tmp на внешний диск
# это путь куда примонтирован внешний диск - замени на актуальный
MNT="/mnt/hdd_data/"

sudo systemctl stop docker
sudo mkdir $MNT/docker
mkdir $MNT/docker/tmp
mkdir $MNT/docker/image
sudo rsync -aHSX /var/lib/docker/image/ $MNT/docker/image/
sudo rsync -aHSX /var/lib/docker/tmp/ $MNT/docker/tmp/
sudo mv /var/lib/docker/image /var/lib/docker/image.old

