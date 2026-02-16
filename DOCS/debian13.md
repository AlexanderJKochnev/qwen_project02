## настройка debian 13
1. удаление графических оболочек (из под su)
    apt purge -y gnome* x11-common xserver-xorg* desktop-base task-gnome-desktop tasksel
    apt purge -y kde* plasma* xfce4* lxde*
    apt autoremove --purge -y
    apt clean
    apt purge -y gdm3 lightdm sddm slim
    apt purge -y libreoffice* thunderbird* gimp* inkscape* vlc*
    apt purge -y fonts-* sound-theme-freedesktop alsa-utils pulseaudio pipewire
    apt autoremove --purge -y
    apt clean
    apt purge -y cups* avahi-daemon modemmanager bluetooth*
    apt autoremove --purge

2. установка htop
    apt install htop
    htop
3. список процессов:
    ps aux --sort=-%mem | head -n 15
4. список сервисов
   systemctl list-units --type=service --state=running
5. установка docker
   apt install -y docker.io docker-compose
   systemctl enable --now docker
   usermod -aG docker alexander
6. просмотр оборудования 
   apt update && sudo apt install inxi
   inxi -Fxz
7. контроль температуры
   apt install lm-sensors
   sensors-quiet
   sensors
8. отключение управлния питанием (для сервера)
   apt install ethtool (не работает)
9. установка git
   apt install git -y
   git config --global user.name "Alexander"
   git config --global user.email "akochnev66@gmail.com"
   ls -l ~/.ssh/id_rsa.pub # проверка ключа
   wssh-keygen -t ed25519 -C "akochnev66@gmail.com"
10. подключение ghcr -> см. ghcr.md
11. подключение HDD ->  скрипт scripts/mounting.sh
12. mkdir wine && cd wine (скопировать .env)
13. git init
14. git remote add qwen git@github.com:AlexanderJKochnev/qwen_project02.git
15. git pull qwen main
16. sh volume_bind.sh
17. скачиваем и устанавливаем backup
18. открывем порты:
    1. ufw allow 80/tcp 
    2. ufw allow 443/tcp
19. 