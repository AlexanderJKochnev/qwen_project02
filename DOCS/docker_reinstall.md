## восстановление docker после краха
1. ## Установка Docker поверх существующих данных на Btrfs
    sudo apt update
    sudo apt install -y docker.io docker-compose btrfs-progs
2. ## Остановите Docker (если запустился автоматически)
    sudo systemctl stop docker.socket
    sudo systemctl stop docker.service
3. ## переименовать созданную директрию при уствновке
    sudo mv /var/lib/docker /var/lib/docker.new_install_backup
4. ## Примонтировать Btrfs-диск с Docker-данными в /var/lib/docker
    echo "UUID=42ca1166-9334-4fc4-8405-c89ebcd3030f /var/lib/docker btrfs defaults,autodefrag,compress=zstd,space_cache=v2 0 0" | sudo tee -a /etc/fstab
    sudo mkdir -p /var/lib/docker
    sudo mount /var/lib/docker