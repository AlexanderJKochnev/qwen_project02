##  useful tips for /etc/fstab
1. sudo nano /etc/fstab
2. /mnt/hdd_data/@named_volumes/lora_trainer/source  /home/alex/dockers/lora_trainer/source  none  bind,x-systemd.requires=/mnt/hdd_data,x-systemd.after=/mnt/hdd_data  0  0
3. sudo mount -a

# ---МОНТИРУЕМ ДИСКИ ---
1. # Посмотрите все диски
    sudo lsblk -f
2. # точка монтирования
    sudo mkdir -p /mnt/hdd_data
3. # Смонтируйте диск временно (для проверки)
   # Если раздел с Btrfs
   sudo mount /dev/nvme1n1p1 /mnt/hdd_data

   # Если ошибка "unknown filesystem type btrfs" — установите btrfs-progs
   sudo apt install -y btrfs-progs
4. sudo mkdir -p /mnt/backups_external
5. sudo mount /dev/sda /mnt/hdd_data
6. Получите UUID диска (для fstab)
   sudo blkid /dev/nvme1n1p1 | grep -oP 'UUID="\K[^"]+'
7. sudo blkid /dev/sda | grep -oP 'UUID="\K[^"]+'
## подключение через fstab
8. sudo nano etc/fstab
9. UUID=42ca1166-9334-4fc4-8405-c89ebcd3030f /mnt/hdd_data btrfs defaults,autodefrag,compress=zstd,space_cache=v2 0 0
10. UUID=bd49248e-a092-46b9-8107-d2e3fcd474ae /mnt/backups_external btrfs defaults,autodefrag,compress=zstd,space_cache=v2 0 0 
11. UUID=cabd6c75-f172-4d8b-9047-084fa0ae46f3 /mnt/backups_external btrfs defaults,autodefrag,compress=zstd,space_cache=v2 0 0