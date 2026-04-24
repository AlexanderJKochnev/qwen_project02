##  переводим docker в полную автономию
#### все образы будут храниться локально
sudo btrfs subvolume create /mnt/hdd_data/@docker_library
# Проверить, что атрибут установлен (должна быть буква 'C' в выводе)
lsattr -d /mnt/hdd_data/@docker_library
# включить сжатие
chattr +c /mnt/hdd_data/@docker_library
# запуск скрипта
1. cd docker_library
2. bash sync_library.sh
# 