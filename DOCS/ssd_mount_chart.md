cat > /home/alex/mount_points_backup.txt << 'EOF'
=== ИНФОРМАЦИЯ О ТОЧКАХ МОНТИРОВАНИЯ ($(date)) ===

СТАРЫЙ ДИСК:
  Устройство: /dev/sda (TOSHIBA MK1059GSM)
  Точка монтирования: /mnt/hdd_data
  UUID: 475f0a2d-db86-4cc7-bb05-74619256fa50
  Использовано: 92.1G / 915.8G
  Файловая система: ext4

  BIND MOUNTS (в fstab):
    /mnt/hdd_data/log → /var/log
    /mnt/hdd_data/volumes → /var/lib/docker/volumes
    /mnt/hdd_data/projects/wine/* → /home/alex/dockers/wine/* (13 путей)

НОВЫЙ ДИСК:
  Устройство: /dev/nvme1n1 (INTEL SSDPE2KX010T7)
  Разделы:
    /dev/nvme1n1p1 (16G) - LVM2_member
    /dev/nvme1n1p2 (915.5G) - crypto_LUKS (зашифрован)

DOCKER:
  data-root: /var/lib/docker
  volumes: 30+ именованных томов (все на /dev/sda через bind mount)

СИСТЕМНЫЕ ДИСКИ:
  /dev/nvme0n1 (Patriot M.2 P320 256GB) - системный диск с LVM
EOF