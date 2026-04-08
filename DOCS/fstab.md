##  useful tips for /etc/fstab
1. sudo nano /etc/fstab
2. /mnt/hdd_data/@named_volumes/lora_trainer/source  /home/alex/dockers/lora_trainer/source  none  bind,x-systemd.requires=/mnt/hdd_data,x-systemd.after=/mnt/hdd_data  0  0
4. sudo mount -a