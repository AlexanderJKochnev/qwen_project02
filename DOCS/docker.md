# for the memory: rare command in docker

1. use customized env file:
   1. docker compose --env-file .env.prod up --build -d
2. use customized docker-compose file
   1. docker compose -f docker-compose.prod.yaml up --build -d
3. use customized prohect_name
   1. docker compose -p super-name-project up --build -d
4. остановка docker
   sudo systemctl stop docker.socket
   sudo systemctl stop docker
5. проверка что docker затих
   sudo systemctl status docker.socket docker.service | grep Active
6. перенос данных
   sudo rsync -aqxP /var/lib/docker/ /mnt/hdd_data/docker/
7. запуск docker
   sudo systemctl start docker
8. права пользщователя 
   sudo chown -R root:root /mnt/hdd_data/docker
   sudo chmod -R 711 /mnt/hdd_data/docker
   sudo usermod -aG docker $USER
9. sudo umount /var/lib/docker/volumes

## Правильное монтирование?
10. sudo mount --bind /mnt/hdd_data/docker /var/lib/docker 
11. sudo mount --bind /mnt/hdd_data/volumes /var/lib/docker/volumes
12. sudo systemctl daemon-reload





