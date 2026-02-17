#!/bin/sh

# Добавление репозиториев и установка драйвера
sudo sed -i 's/main/main non-free contrib/g' /etc/apt/sources.list
sudo apt update
sudo apt install nvidia-driver nvidia-smi -y
# Перезагрузите сервер после установки драйверов
sudo reboot
