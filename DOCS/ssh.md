## подключение по ssh к удаленному linux компьютеру
1. ### Генерация ключей (без passphrase)
    ssh-keygen -t ed25519
2. ### Копирование ключа на Debian 13
    ssh-copy-id user@remote_host
3. ### Настройка файла ~/.ssh/config
    Host my-server
    HostName 1.2.3.4       # IP-адрес или домен сервера
    User your_username    # Имя пользователя на сервере
    IdentityFile ~/.ssh/id_ed25519  # Путь к вашему приватному ключу
4. ### Отключение парольного входа (безопасность)
    sudo nano /etc/ssh/sshd_config
    PasswordAuthentication no
    sudo systemctl restart ssh
