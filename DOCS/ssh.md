## подключение по ssh к удаленному linux компьютеру
1. ###  на сервере 
    sudo apt update
    sudo apt install -y openssh-server
    sudo systemctl status ssh
2. на компне удалиь старый
   ssh-keygen -R 192.168.0.43
   ssh-keygen -R 83.167.126.4:19903
3. ### Генерация ключей (без passphrase)
    ssh-keygen -t ed25519
4. ### Копирование ключа на Debian 13
    ssh-copy-id user@remote_host
5. ### Настройка файла ~/.ssh/config
    Host my-server
    HostName 1.2.3.4       # IP-адрес или домен сервера
    User your_username    # Имя пользователя на сервере
    IdentityFile ~/.ssh/id_ed25519  # Путь к вашему приватному ключу
6. ### Отключение парольного входа (безопасность)
    sudo nano /etc/ssh/sshd_config
    PasswordAuthentication no
    sudo systemctl restart ssh
7. # Добавьте пользователя alex в группу sudo
usermod -aG sudo alex

# Проверьте
groups alex

# Выйдите из root
exit

# Удалить кэш скачанных пакетов (.deb файлы)
sudo apt clean

# Удалить устаревшие кэши (более щадящий вариант)
sudo apt autoclean

# Удалить пакеты, которые были установлены автоматически и больше не нужны
sudo apt autoremove

# Удалить конфигурационные файлы удаленных пакетов (осторожно!)
sudo apt purge $(dpkg -l | grep '^rc' | awk '{print $2}') 2>/dev/null